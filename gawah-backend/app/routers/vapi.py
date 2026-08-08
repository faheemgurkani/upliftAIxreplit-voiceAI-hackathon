from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.db.database import Database, get_db
from app.models.case import CaseCreate
from app.models.statement import StatementRecord, StructuredStatement
from app.models.vapi import (
    VapiCallEndedPayload,
    VapiCallStartedPayload,
    VapiConfirmationPayload,
    VapiTranscriptPayload,
    VapiWebhookEnvelope,
)
from app.services.llm_service import LLMService, get_llm_service
from app.services.statement_builder import (
    generate_case_id,
    generate_readback_text,
    merge_structured,
)

router = APIRouter(prefix="/vapi", tags=["vapi"])


def _language_from_metadata(metadata: Dict[str, Any], default: str = "urdu") -> str:
    lang = metadata.get("language") or metadata.get("witness_language") or default
    if lang not in {"urdu", "punjabi", "pashto", "english"}:
        return default
    return lang


def _case_id_from_metadata(metadata: Dict[str, Any]) -> Optional[str]:
    value = metadata.get("case_id") or metadata.get("caseId")
    return str(value) if value else None


@router.post("/call-started")
async def call_started(
    payload: VapiCallStartedPayload,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    case_id = payload.case_id or generate_case_id()
    existing = db.get_case(case_id)
    if existing is None:
        db.create_case(
            CaseCreate(case_id=case_id, status="in_progress"),
            case_id=case_id,
        )
    else:
        db.update_case_status(case_id, "in_progress")

    statement = StatementRecord(
        case_id=case_id,
        call_sid=payload.call_id,
        witness_language=payload.language,
        raw_transcript="",
    )
    saved = db.save_statement(statement)

    return {
        "ok": True,
        "case_id": case_id,
        "statement_id": saved.id,
        "language": payload.language,
        "message": "Session initialized",
    }


@router.post("/transcript")
async def handle_transcript(
    payload: VapiTranscriptPayload,
    db: Database = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    if not payload.transcript.strip():
        raise HTTPException(status_code=400, detail="Empty transcript")

    case_id = payload.case_id
    existing = db.get_statement_by_call(payload.call_id)
    if case_id is None:
        case_id = existing.case_id if existing else generate_case_id()

    saved = db.append_transcript(
        call_sid=payload.call_id,
        chunk=payload.transcript,
        case_id=case_id,
        language=payload.language,
    )

    if not payload.is_final:
        return {
            "ok": True,
            "partial": True,
            "case_id": case_id,
            "statement_id": saved.id,
        }

    structured = await llm.structure_statement(saved.raw_transcript, payload.language)
    inconsistencies = await llm.flag_inconsistencies(saved.raw_transcript)
    if inconsistencies:
        structured.inconsistencies = list(
            dict.fromkeys([*structured.inconsistencies, *inconsistencies])
        )

    saved.structured_statement = structured
    saved.inconsistencies = structured.inconsistencies
    saved.readback_text = generate_readback_text(structured, payload.language)
    saved = db.save_statement(saved)
    db.update_case_status(case_id, "statement_pending")

    return {
        "ok": True,
        "case_id": case_id,
        "statement_id": saved.id,
        "structured_statement": structured.model_dump(),
        "inconsistencies": saved.inconsistencies,
        "response": saved.readback_text,
    }


@router.post("/call-ended")
async def call_ended(
    payload: VapiCallEndedPayload,
    db: Database = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    existing = db.get_statement_by_call(payload.call_id)
    case_id = payload.case_id or (existing.case_id if existing else generate_case_id())
    language = payload.language

    if existing is None:
        existing = StatementRecord(
            case_id=case_id,
            call_sid=payload.call_id,
            witness_language=language,
            raw_transcript=payload.transcript or "",
        )
    elif payload.transcript:
        existing.raw_transcript = payload.transcript

    structured = await llm.structure_statement(existing.raw_transcript, language)
    if existing.structured_statement:
        structured = merge_structured(existing.structured_statement, structured)

    inconsistencies = await llm.flag_inconsistencies(existing.raw_transcript)
    structured.inconsistencies = list(
        dict.fromkeys([*structured.inconsistencies, *inconsistencies])
    )

    existing.structured_statement = structured
    existing.inconsistencies = structured.inconsistencies
    existing.readback_text = generate_readback_text(structured, language)
    saved = db.save_statement(existing)
    db.update_case_status(case_id, "statement_pending")

    return {
        "ok": True,
        "case_id": case_id,
        "statement_id": saved.id,
        "ended_reason": payload.ended_reason,
        "structured_statement": structured.model_dump(),
        "response": saved.readback_text,
    }


@router.post("/confirmation")
async def confirmation(
    payload: VapiConfirmationPayload,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    statement = None
    if payload.statement_id:
        statement = db.get_statement_by_id(payload.statement_id)
    if statement is None:
        statement = db.get_statement_by_call(payload.call_id)
    if statement is None and payload.case_id:
        statement = db.get_statement_by_case(payload.case_id)
    if statement is None:
        raise HTTPException(status_code=404, detail="Statement not found for confirmation")

    if payload.confirmed:
        statement.confirmed = True
        statement = db.save_statement(statement)
        db.update_case_status(statement.case_id, "in_progress")
        message = "Statement confirmed by witness."
    else:
        message = "Witness rejected the readback; collect corrections."

    return {
        "ok": True,
        "confirmed": payload.confirmed,
        "statement_id": statement.id,
        "case_id": statement.case_id,
        "response": message,
    }


@router.post("/webhook")
async def vapi_native_webhook(
    envelope: VapiWebhookEnvelope,
    db: Database = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    Native Vapi server-url endpoint.

    Accepts { "message": { "type": "...", ... } } and routes internally.
    Point Vapi assistant.server.url to: https://<host>/vapi/webhook
    """
    message = envelope.message
    call_id = (message.call.id if message.call else None) or "unknown-call"
    metadata = {}
    if message.call and message.call.metadata:
        metadata = message.call.metadata
    metadata.update(message.metadata or {})

    language = _language_from_metadata(metadata)
    case_id = _case_id_from_metadata(metadata)

    msg_type = message.type

    if msg_type in {"status-update"} and (message.status == "in-progress" or (message.call and message.call.status == "in-progress")):
        return await call_started(
            VapiCallStartedPayload(
                call_id=call_id,
                language=language,  # type: ignore[arg-type]
                case_id=case_id,
                metadata=metadata,
            ),
            db=db,
        )

    if msg_type == "transcript":
        is_final = (message.transcriptType or "final") == "final"
        return await handle_transcript(
            VapiTranscriptPayload(
                call_id=call_id,
                transcript=message.transcript or "",
                language=language,  # type: ignore[arg-type]
                case_id=case_id,
                role=message.role or "user",
                is_final=is_final,
            ),
            db=db,
            llm=llm,
        )

    if msg_type == "end-of-call-report":
        artifact_transcript = None
        if message.artifact and message.artifact.transcript:
            artifact_transcript = message.artifact.transcript
        return await call_ended(
            VapiCallEndedPayload(
                call_id=call_id,
                language=language,  # type: ignore[arg-type]
                case_id=case_id,
                transcript=artifact_transcript,
                ended_reason=message.endedReason,
            ),
            db=db,
            llm=llm,
        )

    if msg_type == "function-call" and message.functionCall:
        name = message.functionCall.get("name")
        params = message.functionCall.get("parameters") or {}
        if name == "confirm_statement":
            return await confirmation(
                VapiConfirmationPayload(
                    call_id=call_id,
                    case_id=params.get("case_id") or case_id,
                    confirmed=bool(params.get("confirmed", True)),
                    statement_id=params.get("statement_id"),
                ),
                db=db,
            )
        if name == "get_case_status":
            target = params.get("case_id") or case_id
            if not target:
                return {"result": {"error": "case_id required"}}
            record = db.get_case(str(target))
            if record is None:
                return {"result": {"error": "case not found", "case_id": target}}
            from app.services.statement_builder import spoken_case_status

            return {
                "result": {
                    "case_id": record.case_id,
                    "status": record.status,
                    "spoken_status": spoken_case_status(
                        record.case_id, record.status, record.title
                    ),
                }
            }

    return {"received": True, "type": msg_type}
