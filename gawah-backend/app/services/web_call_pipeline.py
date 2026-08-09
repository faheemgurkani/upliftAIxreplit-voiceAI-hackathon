"""Web-browser testimony pipeline: audio upload → STT → structure → statement."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.db.database import Database
from app.models.statement import InconsistencyFlag, SaveStatementArgs, StatementRecord
from app.services.call_tracker import human_label
from app.services.consistency_engine import run_consistency_check
from app.services.corroboration_engine import run_corroboration_analysis
from app.services.llm_service import LLMService
from app.services.statement_builder import (
    build_readback_text,
    delay_flags,
    generate_ref_code,
)
from app.services.uplift_service import UpliftService


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_dialogue(dialogue: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Keep only agent/witness turns with non-empty text."""
    out: List[Dict[str, Any]] = []
    if not dialogue:
        return out
    for i, raw in enumerate(dialogue):
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or "").strip()
        if not text:
            continue
        role = str(raw.get("role") or "").strip().lower()
        if role not in {"agent", "witness"}:
            # Heuristic: unknown → agent if identity hints, else witness
            role = "witness" if "witness" in role or "user" in role else "agent"
        out.append(
            {
                "role": role,
                "text": text,
                "id": str(raw.get("id") or f"{role}-{i}"),
                "at": raw.get("at"),
            }
        )
    return out


def _format_dialogue(dialogue: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for turn in dialogue:
        label = "ایجنٹ" if turn.get("role") == "agent" else "گواہ"
        lines.append(f"{label}: {turn.get('text', '').strip()}")
    return "\n\n".join(lines)


def _witness_text(dialogue: List[Dict[str, Any]]) -> str:
    return " ".join(
        str(t.get("text") or "").strip()
        for t in dialogue
        if t.get("role") == "witness" and str(t.get("text") or "").strip()
    )


def append_event(call: Dict[str, Any], event_type: str, detail: str = "", **extra: Any) -> List[Dict[str, Any]]:
    events = list(call.get("events") or [])
    entry = {
        "at": _now(),
        "type": event_type,
        "detail": detail,
        **extra,
    }
    events.append(entry)
    # Cap log size for local JSON store
    return events[-80:]


async def process_web_recording(
    *,
    call_id: str,
    file_bytes: bytes,
    filename: str,
    language: str,
    db: Database,
    uplift: UpliftService,
    llm: LLMService,
    participant_name: str = "Witness",
    dialogue: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Persist web MediaRecorder audio, transcribe via Uplift STT when available,
    structure into a §161 statement, and update the tracked web call.

    `dialogue` (optional) is a live Agent/Witness chat from LiveKit transcriptions.
    Display uses the full dialogue; field structuring prefers witness-only text.
    """
    call = db.get_call(call_id)
    if not call:
        return {"ok": False, "detail": "Web call not found", "status_code": 404}

    if not file_bytes:
        return {"ok": False, "detail": "Empty audio upload", "status_code": 400}

    dialogue_turns = _normalize_dialogue(dialogue)

    # Save audio under local_audio_dir/calls/{call_id}/
    dest_dir = Path(uplift.settings.local_audio_dir) / "calls" / call_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(filename or "recording.webm").suffix or ".webm"
    if suffix.lower() not in {".webm", ".mp3", ".wav", ".ogg", ".m4a", ".mp4"}:
        suffix = ".webm"
    dest = dest_dir / f"web-recording{suffix}"
    dest.write_bytes(file_bytes)

    events = append_event(
        call,
        "recording_received",
        f"Saved {len(file_bytes)} bytes as {dest.name}"
        + (f"; dialogue turns={len(dialogue_turns)}" if dialogue_turns else ""),
        bytes=len(file_bytes),
    )
    db.upsert_call(
        {
            "call_id": call_id,
            "status": "processing",
            "state": "processing",
            "label": human_label("processing"),
            "local_recording_path": str(dest),
            "artifacts_status": "processing",
            "events": events,
            "channel": call.get("channel") or "web_browser",
            "dialogue": dialogue_turns or None,
        }
    )
    db.record_kpi_event(
        "web_recording_uploaded",
        {"call_id": call_id, "bytes": len(file_bytes), "dialogue_turns": len(dialogue_turns)},
    )

    # STT — Uplift when keyed; otherwise treat as unavailable and keep raw empty
    witness_transcript = ""
    stt_detail = None
    stt = await uplift.transcribe(file_bytes, filename=dest.name)
    if stt.get("ok"):
        witness_transcript = (stt.get("transcript") or "").strip()
        events = append_event(
            {"events": events},
            "stt_complete",
            f"Witness STT length {len(witness_transcript)} chars",
        )
    else:
        stt_detail = stt.get("detail") or "STT unavailable"
        events = append_event(
            {"events": events},
            "stt_failed",
            str(stt_detail)[:300],
        )

    # If live dialogue had no witness lines, append STT as a witness turn
    if witness_transcript and not _witness_text(dialogue_turns):
        dialogue_turns = list(dialogue_turns) + [
            {
                "role": "witness",
                "text": witness_transcript,
                "id": f"stt-witness-{call_id}",
                "at": None,
            }
        ]
        events = append_event(
            {"events": events},
            "dialogue_merged_stt",
            "Appended witness STT into dialogue (no live witness transcriptions)",
        )

    dialogue_text = _format_dialogue(dialogue_turns)
    # Full transcript for display = labelled dialogue when present, else raw STT
    transcript = dialogue_text or witness_transcript
    # Structure §161 from witness speech only (agent questions pollute extraction)
    structure_source = _witness_text(dialogue_turns) or witness_transcript

    # Structure fields from transcript (LLM or heuristic)
    lang = language if language in {"ur", "pa", "ps", "mixed", "en"} else "ur"
    structured = await llm.structure_statement(structure_source or "(empty recording)", lang)

    sequence = structured.sequence_of_events
    if isinstance(sequence, list):
        sequence_text = " ".join(str(s) for s in sequence if s)
    else:
        sequence_text = str(sequence or transcript or "Web testimony recording — pending review.")

    location = structured.incident_location or "unknown (web testimony)"
    if location in {"unknown", ""}:
        location = "unknown (web testimony)"

    time_bits = [
        p
        for p in [structured.incident_date, structured.incident_time]
        if p and p != "unknown"
    ]
    time_of_incident = " ".join(time_bits) if time_bits else None

    persons = list(structured.persons_involved or [])
    persons = [str(p) for p in persons if p and str(p).lower() != "unknown"]

    args = SaveStatementArgs(
        time_of_incident=time_of_incident,
        location=location,
        persons_present=persons,
        sequence_of_events=sequence_text or transcript or "Web recording received.",
        relationship_to_accused=None,
        temporal_uncertainty=True,
        language_of_call=lang if lang != "en" else "ur",
        witness_type="unknown",
        session_id=call_id,
    )

    existing = db.get_statement_by_session(call_id)
    ref_code = existing.ref_code if existing else generate_ref_code()
    delay_meta = delay_flags(None)

    inconsistency_flags: List[InconsistencyFlag] = []
    if existing:
        inconsistency_flags = list(existing.inconsistency_flags or [])
    for item in structured.inconsistencies or []:
        inconsistency_flags.append(
            InconsistencyFlag(
                source="web_pipeline",
                contradiction_description=str(item),
                contradiction_type="unknown",
            )
        )

    record = StatementRecord(
        ref_code=ref_code,
        session_id=call_id,
        time_of_incident=args.time_of_incident,
        location=args.location,
        persons_present=args.persons_present,
        sequence_of_events=args.sequence_of_events,
        relationship_to_accused=args.relationship_to_accused,
        temporal_uncertainty=True,
        language_of_call=args.language_of_call,
        witness_type=args.witness_type,
        delayed_statement_high_risk=delay_meta.get("delayed_statement_high_risk", False),
        privacy_mode=existing.privacy_mode if existing else False,
        intimidation_flag=existing.intimidation_flag if existing else False,
        intimidation_text=existing.intimidation_text if existing else None,
        inconsistency_flags=inconsistency_flags,
        status="pending_review",
        call_recording_url=str(dest),
        raw_transcript=transcript or witness_transcript or None,
    )
    if existing:
        record.id = existing.id
        record.created_at = existing.created_at

    readback = build_readback_text(args)
    record.readback_text = readback
    audio_url = await uplift.store_readback_audio(ref_code, readback)
    record.readback_audio_url = audio_url
    saved = db.save_statement(record)

    events = append_event(
        {"events": events},
        "statement_saved",
        f"Reference {ref_code}",
        ref_code=ref_code,
    )
    db.upsert_call(
        {
            "call_id": call_id,
            "status": "completed",
            "state": "completed",
            "label": "Completed — web testimony processed",
            "connected": True,
            "ended_at": _now(),
            "ended_by": "web_pipeline",
            "transcript": transcript or None,
            "witness_transcript": witness_transcript or None,
            "dialogue": dialogue_turns or None,
            "local_recording_path": str(dest),
            "recording_url": None,
            "artifacts_available": True,
            "artifacts_status": "ready",
            "ref_code": ref_code,
            "participant_name": participant_name,
            "events": events,
            "analysis": {
                "source": "web_pipeline",
                "stt_ok": bool(stt.get("ok")),
                "stt_detail": stt_detail,
                "dialogue_turns": len(dialogue_turns),
                "structured": structured.model_dump(),
            },
            "channel": "web_browser",
            "direction": "inbound",
            "mocked": bool(call.get("mocked", False)),
        }
    )
    db.record_kpi_event(
        "statement_saved",
        {"ref_code": ref_code, "language": args.language_of_call, "channel": "web_browser"},
    )
    db.record_kpi_event("web_call_completed", {"call_id": call_id, "ref_code": ref_code})

    # Post-save engines (same as phone tool path) — never fail the upload
    try:
        await run_consistency_check(ref_code)
        await run_corroboration_analysis(ref_code)
        events = append_event({"events": events}, "post_analysis_done", "Consistency + corroboration ran")
        db.upsert_call({"call_id": call_id, "events": events})
    except Exception as exc:  # noqa: BLE001
        events = append_event(
            {"events": events},
            "post_analysis_skipped",
            str(exc)[:240],
        )
        db.upsert_call({"call_id": call_id, "events": events})

    return {
        "ok": True,
        "call_id": call_id,
        "ref_code": ref_code,
        "status": "completed",
        "transcript": transcript,
        "witness_transcript": witness_transcript,
        "dialogue": dialogue_turns,
        "readback_text": readback,
        "statement_id": saved.id,
        "local_recording_path": str(dest),
        "stt_ok": bool(stt.get("ok")),
        "stt_detail": stt_detail,
        "label": "Completed — web testimony processed",
    }
