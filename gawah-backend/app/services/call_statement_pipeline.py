"""Call → statement bridge: stream completed call artifacts into the dashboard.

Used when a live call ends with transcript/recording but the agent did not
invoke save_witness_statement (common for PSTN). Web tool-path and web-recorder
path already create statements; this fills the telephony gap so dashboard
lists stay live for real operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.db.database import Database
from app.models.statement import InconsistencyFlag, SaveStatementArgs, StatementRecord
from app.services.call_tracker import TERMINAL_STATES, human_label
from app.services.consistency_engine import run_consistency_check
from app.services.corroboration_engine import run_corroboration_analysis
from app.services.llm_service import LLMService
from app.services.statement_builder import (
    build_readback_text,
    delay_flags,
    generate_ref_code,
)
from app.services.uplift_service import UpliftService
from app.services.web_call_pipeline import append_event


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_phone_channel(channel: Optional[str]) -> bool:
    ch = (channel or "").lower()
    return any(x in ch for x in ("phone", "telephony", "pstn"))


def _has_statement_material(call: Dict[str, Any]) -> bool:
    transcript = (call.get("transcript") or "").strip()
    if transcript:
        return True
    if call.get("local_recording_path"):
        return True
    if call.get("recording_url"):
        return True
    return False


async def _resolve_transcript(
    call: Dict[str, Any],
    *,
    uplift: UpliftService,
) -> tuple[str, Optional[str], Optional[str]]:
    """Return (transcript, stt_detail, local_recording_path)."""
    transcript = (call.get("transcript") or "").strip()
    local_path = call.get("local_recording_path")
    stt_detail = None

    if transcript:
        return transcript, None, local_path

    if local_path and Path(str(local_path)).is_file():
        raw = Path(str(local_path)).read_bytes()
        stt = await uplift.transcribe(raw, filename=Path(str(local_path)).name)
        if stt.get("ok"):
            return (stt.get("transcript") or "").strip(), None, local_path
        stt_detail = str(stt.get("detail") or "STT unavailable")[:300]
        return "", stt_detail, local_path

    return "", stt_detail, local_path


async def ensure_statement_from_call(
    *,
    call_id: str,
    db: Database,
    uplift: UpliftService,
    llm: LLMService,
    language: str = "ur",
    force: bool = False,
) -> Dict[str, Any]:
    """
    Ensure a completed call with usable artifacts has a dashboard statement.

    Idempotent: if a statement already exists for the session/call, links
    `ref_code` onto the call row and returns it.
    """
    call = db.get_call(call_id)
    if not call:
        return {"ok": False, "detail": "Call not found", "status_code": 404}

    # Already linked
    existing_ref = call.get("ref_code")
    if existing_ref and not force:
        stmt = db.get_statement_by_ref(str(existing_ref))
        if stmt:
            return {
                "ok": True,
                "skipped": True,
                "reason": "already_linked",
                "call_id": call_id,
                "ref_code": stmt.ref_code,
            }

    # Statement created via tools during the call
    by_session = db.get_statement_by_session(call_id)
    if by_session and not force:
        events = append_event(
            call,
            "statement_linked",
            f"Linked existing tool-path statement {by_session.ref_code}",
            ref_code=by_session.ref_code,
        )
        db.upsert_call(
            {
                "call_id": call_id,
                "ref_code": by_session.ref_code,
                "events": events,
                "statement_pipeline_status": "linked",
            }
        )
        return {
            "ok": True,
            "skipped": True,
            "reason": "linked_existing_statement",
            "call_id": call_id,
            "ref_code": by_session.ref_code,
        }

    status = (call.get("status") or call.get("state") or "").lower()
    if status not in TERMINAL_STATES and status != "processing" and not force:
        return {
            "ok": False,
            "skipped": True,
            "reason": "call_not_terminal",
            "call_id": call_id,
            "status": status,
        }

    # Failed / no-answer calls never produce statements
    if status == "failed" and not force:
        return {
            "ok": False,
            "skipped": True,
            "reason": "failed_call",
            "call_id": call_id,
        }

    # Demo/mocked rows without material stay demo-only
    if call.get("mocked") and not _has_statement_material(call) and not force:
        return {
            "ok": False,
            "skipped": True,
            "reason": "mocked_without_artifacts",
            "call_id": call_id,
        }

    if not _has_statement_material(call) and not force:
        return {
            "ok": False,
            "skipped": True,
            "reason": "no_transcript_or_recording",
            "call_id": call_id,
        }

    # Mark processing so list sync does not double-fire
    events = append_event(call, "statement_pipeline_start", "Building dashboard statement from call")
    db.upsert_call(
        {
            "call_id": call_id,
            "status": "processing" if status == "completed" else status,
            "state": "processing" if status == "completed" else call.get("state") or status,
            "label": human_label("processing", channel=call.get("channel")),
            "statement_pipeline_status": "processing",
            "events": events,
        }
    )

    transcript, stt_detail, local_path = await _resolve_transcript(call, uplift=uplift)
    if not transcript and not force:
        events = append_event(
            {"events": events},
            "statement_pipeline_skipped",
            stt_detail or "No transcript available yet",
        )
        db.upsert_call(
            {
                "call_id": call_id,
                "status": "completed",
                "state": "completed",
                "label": human_label("completed", channel=call.get("channel")),
                "statement_pipeline_status": "awaiting_transcript",
                "events": events,
            }
        )
        return {
            "ok": False,
            "skipped": True,
            "reason": "awaiting_transcript",
            "call_id": call_id,
            "stt_detail": stt_detail,
        }

    lang = language if language in {"ur", "pa", "ps", "mixed", "en"} else "ur"
    structured = await llm.structure_statement(
        transcript or "(empty call transcript)",
        lang,
    )

    sequence = structured.sequence_of_events
    if isinstance(sequence, list):
        sequence_text = " ".join(str(s) for s in sequence if s)
    else:
        sequence_text = str(
            sequence
            or transcript
            or "Phone testimony — pending review."
        )

    location = structured.incident_location or "unknown (phone testimony)"
    if location in {"unknown", ""}:
        location = "unknown (phone testimony)"

    time_bits = [
        p
        for p in [structured.incident_date, structured.incident_time]
        if p and p != "unknown"
    ]
    time_of_incident = " ".join(time_bits) if time_bits else None
    persons = [
        str(p)
        for p in (structured.persons_involved or [])
        if p and str(p).lower() != "unknown"
    ]

    args = SaveStatementArgs(
        time_of_incident=time_of_incident,
        location=location,
        persons_present=persons,
        sequence_of_events=sequence_text or transcript or "Call recording received.",
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
                source="call_pipeline",
                contradiction_description=str(item),
                contradiction_type="unknown",
            )
        )

    channel = call.get("channel") or "phone_outbound"
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
        call_recording_url=str(local_path) if local_path else call.get("recording_url"),
        raw_transcript=transcript or None,
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
            "label": "Completed — statement on dashboard",
            "connected": True if call.get("connected") is None else call.get("connected"),
            "ended_at": call.get("ended_at") or _now(),
            "transcript": transcript or call.get("transcript"),
            "local_recording_path": local_path or call.get("local_recording_path"),
            "artifacts_available": True,
            "artifacts_status": call.get("artifacts_status") or "ready",
            "ref_code": ref_code,
            "statement_pipeline_status": "done",
            "events": events,
            "analysis": {
                "source": "call_statement_pipeline",
                "stt_detail": stt_detail,
                "structured": structured.model_dump(),
                "channel": channel,
            },
            "channel": channel,
        }
    )
    db.record_kpi_event(
        "statement_saved",
        {"ref_code": ref_code, "language": args.language_of_call, "channel": channel},
    )
    db.record_kpi_event(
        "call_statement_streamed",
        {"call_id": call_id, "ref_code": ref_code, "channel": channel},
    )

    try:
        await run_consistency_check(ref_code)
        await run_corroboration_analysis(ref_code)
        events = append_event(
            {"events": events},
            "post_analysis_done",
            "Consistency + corroboration ran",
        )
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
        "readback_text": readback,
        "statement_id": saved.id,
        "channel": channel,
        "phone_channel": _is_phone_channel(channel),
        "stt_detail": stt_detail,
        "label": "Completed — statement on dashboard",
    }


async def maybe_stream_call_to_dashboard(
    *,
    call: Dict[str, Any],
    db: Database,
    uplift: UpliftService,
    llm: LLMService,
) -> Optional[Dict[str, Any]]:
    """
    Best-effort auto-stream for terminal phone calls during /calls sync.
    Returns None when nothing to do.
    """
    call_id = str(call.get("call_id") or "")
    if not call_id:
        return None

    status = (call.get("status") or "").lower()
    channel = str(call.get("channel") or "")
    pipeline_status = call.get("statement_pipeline_status")

    if call.get("ref_code"):
        return None
    if pipeline_status in {"done", "linked", "processing"}:
        return None
    if status != "completed":
        return None
    # Auto-stream phone/PSTN only — web uses recorder + client tools
    if not _is_phone_channel(channel):
        return None
    if not _has_statement_material(call):
        return None

    return await ensure_statement_from_call(
        call_id=call_id,
        db=db,
        uplift=uplift,
        llm=llm,
    )
