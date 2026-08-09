from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.db.database import Database, get_db
from app.models.statement import InconsistencyFlag, SaveStatementArgs, StatementRecord
from app.services.consistency_engine import run_consistency_check
from app.services.corroboration_engine import run_corroboration_analysis
from app.services.edge_cases import detect_intimidation_text
from app.services.ngo_webhook import notify_ngo
from app.services.protection_service import (
    assess_protection,
    generate_protection_referral_pdf,
)
from app.services.statement_builder import (
    build_readback_text,
    delay_flags,
    generate_ref_code,
)
from app.services.uplift_service import UpliftService, get_uplift_service

router = APIRouter(prefix="/api/tools", tags=["tools"])


class ToolEnvelope(BaseModel):
    """Flexible tool payload from Uplift / demo client."""

    session_id: Optional[str] = None
    roomName: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    raw_arguments: Dict[str, Any] = Field(default_factory=dict)


def _args(payload: ToolEnvelope) -> Dict[str, Any]:
    return payload.raw_arguments or payload.arguments or {}


def _session_id(payload: ToolEnvelope) -> str:
    return payload.session_id or payload.roomName or "default-session"


async def _post_save_jobs(ref_code: str) -> None:
    await run_consistency_check(ref_code)
    await run_corroboration_analysis(ref_code)


@router.post("/save_witness_statement")
async def save_witness_statement(
    payload: ToolEnvelope,
    background: BackgroundTasks,
    db: Database = Depends(get_db),
    uplift: UpliftService = Depends(get_uplift_service),
) -> Dict[str, Any]:
    try:
        args = SaveStatementArgs.model_validate(_args(payload))
        session_id = _session_id(payload)
        existing = db.get_statement_by_session(session_id)
        ref_code = existing.ref_code if existing else generate_ref_code()

        delay_meta = delay_flags(args.statement_delay_days)
        record = StatementRecord(
            ref_code=ref_code,
            session_id=session_id,
            time_of_incident=args.time_of_incident,
            location=args.location,
            persons_present=args.persons_present,
            sequence_of_events=args.sequence_of_events,
            relationship_to_accused=args.relationship_to_accused,
            temporal_uncertainty=args.temporal_uncertainty,
            language_of_call=args.language_of_call,
            witness_type=args.witness_type,
            corroboration_sources_mentioned=args.corroboration_sources_mentioned,
            statement_delay_days=args.statement_delay_days,
            statement_delay_explanation=args.statement_delay_explanation,
            delayed_statement_high_risk=delay_meta.get("delayed_statement_high_risk", False),
            privacy_mode=existing.privacy_mode if existing else False,
            intimidation_flag=existing.intimidation_flag if existing else False,
            intimidation_text=existing.intimidation_text if existing else None,
            inconsistency_flags=existing.inconsistency_flags if existing else [],
            status="pending_review",
        )
        if existing:
            record.id = existing.id
            record.created_at = existing.created_at

        readback = build_readback_text(args)
        record.readback_text = readback
        audio_url = await uplift.store_readback_audio(ref_code, readback)
        record.readback_audio_url = audio_url
        saved = db.save_statement(record)
        db.record_kpi_event(
            "statement_saved",
            {"ref_code": ref_code, "language": args.language_of_call},
        )

        # Stream statement onto the tracked call row so /calls ↔ /dashboard stay linked
        tracked = db.get_call(session_id)
        if tracked:
            from datetime import datetime, timezone

            events = list(tracked.get("events") or [])
            events.append(
                {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "type": "statement_saved",
                    "detail": f"Tool path saved statement {ref_code}",
                    "ref_code": ref_code,
                }
            )
            db.upsert_call(
                {
                    "call_id": session_id,
                    "ref_code": ref_code,
                    "statement_pipeline_status": "linked",
                    "events": events[-80:],
                    "label": tracked.get("label") or "Statement on dashboard",
                }
            )

        # Background: Section 16 + 17 (never block the call)
        background.add_task(_post_save_jobs, ref_code)

        presentation = (
            "Theek hai. Ab main aap ka bayan dohraunga. Ghoor se sunein aur batain: "
            f"kya yeh sahi hai?\n\n{readback}\n\n"
            f"Aap ka reference code hai: {ref_code}. Yahi code yaad rakhein — "
            f"{ref_code} — {ref_code}."
        )
        return {
            "result": {"refCode": ref_code, "readbackText": readback, "statement_id": saved.id},
            "presentationInstructions": presentation,
        }
    except Exception as err:  # noqa: BLE001
        return {
            "error": str(err),
            "presentationInstructions": (
                "Mujhe khed hai, bayan mehfooz karne mein masla aaya. "
                "Kya aap dobara koshish karenge?"
            ),
        }


@router.post("/flag_inconsistency")
async def flag_inconsistency(
    payload: ToolEnvelope,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    try:
        args = _args(payload)
        flag = InconsistencyFlag(
            source="realtime",
            contradiction_description=args.get("contradiction_description", ""),
            segment_a=args.get("segment_a", ""),
            segment_b=args.get("segment_b", ""),
            contradiction_type=args.get("contradiction_type", "unknown"),
            category=args.get("contradiction_type", "unknown"),
            legal_risk="Defence may use this for CrPC 162 cross-examination.",
        )
        db.append_inconsistency_flag(_session_id(payload), flag)
        db.record_kpi_event("realtime_inconsistency", {"session_id": _session_id(payload)})
        return {"result": {"flagged": True}, "presentationInstructions": ""}
    except Exception:  # noqa: BLE001
        return {"result": {"flagged": False}, "presentationInstructions": ""}


@router.post("/flag_intimidation")
async def flag_intimidation(
    payload: ToolEnvelope,
    background: BackgroundTasks,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    try:
        args = _args(payload)
        text = args.get("witness_statement", "")
        session_id = _session_id(payload)
        stmt = db.get_statement_by_session(session_id)
        if stmt is None:
            stmt = StatementRecord(
                ref_code=generate_ref_code(),
                session_id=session_id,
                location="pending",
                sequence_of_events="pending",
            )
        stmt.intimidation_flag = True
        stmt.intimidation_text = text
        stmt.status = "urgent_escalation"
        db.save_statement(stmt)
        db.record_kpi_event("intimidation_flagged", {"ref_code": stmt.ref_code})

        background.add_task(
            notify_ngo,
            "INTIMIDATION_DETECTED",
            {
                "session_id": session_id,
                "ref_code": stmt.ref_code,
                "witness_statement": text,
            },
        )
        return {"result": {"escalated": True}, "presentationInstructions": ""}
    except Exception:  # noqa: BLE001
        return {"result": {"escalated": False}, "presentationInstructions": ""}


@router.post("/enable_privacy_mode")
async def enable_privacy_mode(
    payload: ToolEnvelope,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    try:
        session_id = _session_id(payload)
        stmt = db.get_statement_by_session(session_id)
        if stmt is None:
            stmt = StatementRecord(
                ref_code=generate_ref_code(),
                session_id=session_id,
                location="pending",
                sequence_of_events="pending",
                privacy_mode=True,
                status="incomplete",
            )
        else:
            stmt.privacy_mode = True
        db.save_statement(stmt)
        db.record_kpi_event("privacy_mode", {"ref_code": stmt.ref_code})
        return {
            "result": {"privacy_mode": True},
            "presentationInstructions": (
                "Theek hai. Aap ki pehchaan bilkul mehfooz rahegi. "
                "Koi naam, pata, ya shakhsi maloomat nahi puchi jayegi."
            ),
        }
    except Exception:  # noqa: BLE001
        return {"result": {"privacy_mode": False}, "presentationInstructions": ""}


@router.post("/assess_protection_need")
async def assess_protection_need(
    payload: ToolEnvelope,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    args = _args(payload)
    assessment = assess_protection(
        offence_type=args.get("offence_type", "other"),
        witness_is_victim=bool(args.get("witness_is_victim")),
        witness_appears_under_16=bool(args.get("witness_appears_under_16")),
        intimidation_already_flagged=bool(args.get("intimidation_already_flagged")),
        province=args.get("province", "unknown"),
    )
    session_id = _session_id(payload)
    stmt = db.get_statement_by_session(session_id)
    if stmt is None:
        stmt = StatementRecord(
            ref_code=generate_ref_code(),
            session_id=session_id,
            location="pending",
            sequence_of_events="pending",
        )
    stmt.offence_category = args.get("offence_type")
    stmt.witness_is_victim = bool(args.get("witness_is_victim"))
    stmt.witness_age_under_16 = bool(args.get("witness_appears_under_16"))
    if assessment["qualifies"]:
        stmt.protection_referral_generated = True
        stmt.applicable_protection_act = assessment["applicable_act"]
        pdf_path = generate_protection_referral_pdf(
            stmt, assessment["applicable_act"] or ""
        )
        stmt.protection_referral_url = pdf_path
        if stmt.status != "urgent_escalation":
            stmt.status = "urgent_escalation"
    db.save_statement(stmt)
    db.record_kpi_event(
        "protection_assessed",
        {"ref_code": stmt.ref_code, "qualifies": assessment["qualifies"]},
    )
    return {
        "result": {
            "qualifies": assessment["qualifies"],
            "applicable_act": assessment["applicable_act"],
            "grounds": assessment["grounds"],
        },
        "presentationInstructions": assessment["presentationInstructions"],
    }


@router.post("/confirm_statement")
async def confirm_statement(
    payload: ToolEnvelope,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    """Witness spoken confirmation (haan) — no signature/thumbprint."""
    args = _args(payload)
    confirmed = bool(args.get("confirmed", True))
    session_id = _session_id(payload)
    stmt = db.get_statement_by_session(session_id)
    if stmt is None and args.get("ref_code"):
        stmt = db.get_statement_by_ref(str(args["ref_code"]))
    if stmt is None:
        return {
            "result": {"confirmed": False},
            "presentationInstructions": "Statement not found.",
        }
    if confirmed:
        stmt.confirmed_by_witness = True
        db.save_statement(stmt)
        db.record_kpi_event("witness_confirmed", {"ref_code": stmt.ref_code})
        return {
            "result": {"confirmed": True, "refCode": stmt.ref_code},
            "presentationInstructions": "Shukriya. Aap ka bayan tasdeeq ho gaya.",
        }
    stmt.corrections_count += 1
    db.save_statement(stmt)
    return {
        "result": {"confirmed": False, "corrections_count": stmt.corrections_count},
        "presentationInstructions": "Theek hai — batain kya galat hai, main durust karunga.",
    }


@router.post("/detect_intimidation_text")
async def detect_intimidation(payload: Dict[str, str]) -> Dict[str, Any]:
    text = payload.get("text", "")
    return {"triggered": detect_intimidation_text(text)}
