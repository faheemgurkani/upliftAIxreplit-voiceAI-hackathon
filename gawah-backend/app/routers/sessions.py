from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db.database import Database, get_db
from app.services.call_tracker import (
    ACTIVE_STATES,
    TERMINAL_STATES,
    human_label,
    index_remote_sessions,
    merge_uplift_session,
    normalize_call_status,
    persistable_fields,
)
from app.services.phone_utils import CALL_INSTRUCTIONS, normalize_pakistan_phone
from app.services.uplift_service import UpliftService, get_uplift_service


async def _sync_one_call(
    *,
    call_id: str,
    local: Dict[str, Any],
    remote: Optional[Dict[str, Any]],
    uplift: UpliftService,
    db: Database,
    fetch_detail: bool = True,
) -> Dict[str, Any]:
    """Merge list/detail Uplift data into a tracked call and persist artifacts."""
    # Local-only failure stubs (dispatch errors) have no Uplift session to fetch.
    if str(call_id).startswith("failed-"):
        status = local.get("status") or local.get("state") or "failed"
        if status in {"unknown", ""}:
            status = "failed"
        repaired = {
            **local,
            "call_id": call_id,
            "status": status,
            "state": local.get("state") or "failed",
            "label": local.get("label")
            or human_label(status, local.get("outcome") or "dispatch_error"),
            "mocked": bool(local.get("mocked", False)),
            "artifacts_available": False,
            "artifacts_status": "n/a",
        }
        db.upsert_call(persistable_fields(repaired))
        return repaired

    remote_payload = dict(remote or {})
    artifacts = None

    status_hint = (remote_payload.get("state") or local.get("status") or "").lower()
    needs_detail = fetch_detail and (
        status_hint in TERMINAL_STATES
        or (local.get("status") or "").lower() in TERMINAL_STATES
        or not local.get("duration_sec")
        or not local.get("artifacts_status")
        or local.get("artifacts_status") == "pending_or_unavailable"
    )

    if needs_detail and uplift.enabled:
        enriched = await uplift.enrich_call_from_uplift(
            call_id,
            download=not bool(local.get("local_recording_path")),
        )
        if enriched.get("ok"):
            remote_payload = {**remote_payload, **(enriched.get("session") or {})}
            artifacts = enriched.get("artifacts")

    if not remote_payload:
        status = local.get("status") or local.get("state") or "unknown"
        return {
            **local,
            "call_id": call_id,
            "status": status,
            "label": local.get("label")
            or human_label(status, local.get("outcome")),
            "mocked": bool(local.get("mocked", False)),
        }

    merged = merge_uplift_session(local, remote_payload, artifacts=artifacts)
    merged["call_id"] = call_id
    db.upsert_call(persistable_fields(merged))
    return merged

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionCreateBody(BaseModel):
    participantName: str = Field(default="Witness", alias="participantName")
    participant_name: Optional[str] = None

    model_config = {"populate_by_name": True}


class PlaceCallBody(BaseModel):
    to: str = Field(..., description="Pakistani mobile: +92300… or 0300…")
    participantName: Optional[str] = Field(default="Witness", alias="participantName")
    participant_name: Optional[str] = None
    idempotency_key: Optional[str] = None

    model_config = {"populate_by_name": True}


@router.post("/create")
async def create_session(
    body: SessionCreateBody | None = None,
    uplift: UpliftService = Depends(get_uplift_service),
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    name = "Witness"
    if body:
        name = body.participant_name or body.participantName or "Witness"
    session = await uplift.create_session(name)
    db.save_session(
        {
            "room_name": session.get("roomName"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "demo": session.get("demo", False),
            "channel": "browser",
        }
    )
    db.record_kpi_event("session_created", {"room": session.get("roomName")})
    return {
        "token": session.get("token"),
        "wsUrl": session.get("wsUrl"),
        "ws_url": session.get("wsUrl"),
        "roomName": session.get("roomName"),
        "room_name": session.get("roomName"),
        "assistantId": session.get("assistantId"),
        "demo": session.get("demo", False),
        "ok": session.get("ok", True),
        "detail": session.get("detail"),
        "channel": "browser",
    }


@router.post("/call")
async def place_phone_call(
    body: PlaceCallBody,
    uplift: UpliftService = Depends(get_uplift_service),
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    """
    Real outbound PSTN call via Uplift AI (Singapore) — not mocked.

    `dispatched` only means dialing started. Track progress via
    GET /api/sessions/calls (state: dispatched→ringing→answered→completed|failed).
    """
    e164, err = normalize_pakistan_phone(body.to)
    if err or not e164:
        raise HTTPException(status_code=400, detail=err or "Invalid phone number")

    # Soft guard: warn if another call may still be active (Uplift org limit = 1)
    active = [
        c
        for c in db.list_calls(limit=20)
        if (c.get("status") or c.get("state") or "").lower() in ACTIVE_STATES
    ]

    name = body.participant_name or body.participantName or "Witness"
    result = await uplift.place_call(
        e164,
        additional_instructions=CALL_INSTRUCTIONS,
        variables={"participantName": name, "channel": "phone"},
        idempotency_key=body.idempotency_key,
    )
    if not result.get("ok"):
        status = int(result.get("status_code") or 502)
        if status < 400:
            status = 502
        # Persist failed attempt for dashboard visibility
        db.upsert_call(
            {
                "call_id": f"failed-{datetime.now(timezone.utc).timestamp()}",
                "to": e164,
                "status": "failed",
                "state": "failed",
                "outcome": "dispatch_error",
                "failure_reason": str(result.get("detail"))[:500],
                "channel": "phone_outbound",
                "label": human_label("failed", "dispatch_error"),
                "mocked": False,
            }
        )
        raise HTTPException(
            status_code=min(status, 599),
            detail=result.get("detail") or "Failed to place call",
        )

    call_id = result.get("callId")
    tracked = db.upsert_call(
        {
            "call_id": call_id,
            "to": e164,
            "status": "dispatched",
            "state": result.get("status", "dispatched"),
            "channel": "phone_outbound",
            "direction": "outbound",
            "assistant_id": result.get("assistantId"),
            "participant_name": name,
            "mocked": False,
            "label": human_label("dispatched"),
        }
    )
    db.record_kpi_event(
        "call_placed",
        {"call_id": call_id, "to": e164, "status": "dispatched"},
    )
    return {
        "ok": True,
        "mocked": False,
        "callId": call_id,
        "status": "dispatched",
        "to": e164,
        "assistantId": result.get("assistantId"),
        "channel": "phone_outbound",
        "label": tracked.get("label"),
        "active_calls_warning": len(active) > 0,
        "message": (
            "Real Uplift call dispatched (not mocked). Answer your phone. "
            "Track status on Dashboard → Calls. "
            "Note: dispatched ≠ answered — if you miss it, outcome becomes no_answer."
        ),
    }


@router.get("/calls")
async def list_phone_calls(
    limit: int = Query(25, ge=1, le=100),
    sync: bool = Query(True, description="Refresh status + artifacts from Uplift"),
    uplift: UpliftService = Depends(get_uplift_service),
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    """Tracked calls with live Uplift status / metadata sync for the dashboard."""
    local = db.list_calls(limit=limit)
    remote_index: Dict[str, Dict[str, Any]] = {}
    sync_error = None

    if sync and uplift.enabled:
        remote = await uplift.list_call_sessions(limit=max(limit, 20))
        if remote.get("ok"):
            remote_index = index_remote_sessions(remote.get("items") or [])
            # Upsert any telephony sessions we don't have locally yet
            for sid, item in remote_index.items():
                if item.get("channel") != "telephony" and item.get("direction") != "outbound":
                    if not item.get("toNumber"):
                        continue
                if not db.get_call(sid):
                    status = normalize_call_status(
                        state=item.get("state"),
                        outcome=item.get("outcome"),
                        failure_reason=item.get("failureReason"),
                        connected=item.get("connected"),
                    )
                    db.upsert_call(
                        {
                            "call_id": sid,
                            "to": item.get("toNumber"),
                            "from_number": item.get("fromNumber"),
                            "status": status,
                            "state": item.get("state"),
                            "outcome": item.get("outcome"),
                            "failure_reason": item.get("failureReason"),
                            "connected": item.get("connected"),
                            "duration_sec": item.get("durationSec"),
                            "ended_at": item.get("endedAt"),
                            "ended_by": item.get("endedBy"),
                            "channel": item.get("channel") or "phone_outbound",
                            "direction": item.get("direction") or "outbound",
                            "mocked": False,
                            "label": human_label(
                                status,
                                item.get("outcome")
                                if isinstance(item.get("outcome"), str)
                                else None,
                            ),
                            "created_at": item.get("createdAt")
                            or item.get("startedAt")
                            or datetime.now(timezone.utc).isoformat(),
                        }
                    )
            local = db.list_calls(limit=limit)
        else:
            sync_error = remote.get("detail")

    items = []
    # Detail-fetch only for terminal/recent rows to stay polite on Uplift rate limits
    detail_budget = 8
    for call in local:
        cid = str(call.get("call_id") or "")
        if not cid:
            continue
        remote = remote_index.get(cid)
        if sync and uplift.enabled and (remote or call.get("status") in TERMINAL_STATES):
            use_detail = detail_budget > 0
            if use_detail:
                detail_budget -= 1
            merged = await _sync_one_call(
                call_id=cid,
                local=call,
                remote=remote,
                uplift=uplift,
                db=db,
                fetch_detail=use_detail,
            )
            items.append(merged)
        elif remote:
            merged = merge_uplift_session(call, remote)
            db.upsert_call(persistable_fields({**merged, "call_id": cid}))
            items.append(merged)
        else:
            status = call.get("status") or call.get("state") or "unknown"
            items.append(
                {
                    **call,
                    "status": status,
                    "label": call.get("label")
                    or human_label(status, call.get("outcome")),
                    "mocked": bool(call.get("mocked", False)),
                }
            )

    counts = {
        "total": len(items),
        "active": sum(1 for i in items if (i.get("status") or "").lower() in ACTIVE_STATES),
        "completed": sum(1 for i in items if (i.get("status") or "").lower() == "completed"),
        "failed": sum(1 for i in items if (i.get("status") or "").lower() == "failed"),
        "with_artifacts": sum(1 for i in items if i.get("artifacts_available")),
    }

    return {
        "ok": True,
        "mocked": False,
        "sync_error": sync_error,
        "counts": counts,
        "items": items,
        "note": (
            "Uplift session metadata is always synced. Recording/transcript URLs are "
            "captured when the platform exposes them (docs: async after call ends)."
        ),
    }


@router.get("/calls/{call_id}")
async def get_phone_call(
    call_id: str,
    uplift: UpliftService = Depends(get_uplift_service),
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    local = db.get_call(call_id)
    remote_item = None
    if uplift.enabled:
        detail = await uplift.get_session(call_id)
        if detail.get("ok"):
            remote_item = detail.get("session")
        else:
            remote = await uplift.list_call_sessions(limit=30)
            if remote.get("ok"):
                remote_item = index_remote_sessions(remote.get("items") or []).get(call_id)

    if local is None and remote_item is None:
        raise HTTPException(status_code=404, detail="Call not found")

    base = local or {
        "call_id": call_id,
        "to": remote_item.get("toNumber") if remote_item else None,
        "mocked": False,
    }
    merged = await _sync_one_call(
        call_id=call_id,
        local=base,
        remote=remote_item,
        uplift=uplift,
        db=db,
        fetch_detail=True,
    )
    return {"ok": True, "mocked": False, "item": merged}


@router.post("/calls/{call_id}/refresh-artifacts")
async def refresh_call_artifacts(
    call_id: str,
    uplift: UpliftService = Depends(get_uplift_service),
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    """Force re-fetch of Uplift session detail + recording/transcript if present."""
    local = db.get_call(call_id) or {"call_id": call_id, "mocked": False}
    if not uplift.enabled:
        raise HTTPException(status_code=503, detail="Uplift not configured")
    merged = await _sync_one_call(
        call_id=call_id,
        local=local,
        remote=None,
        uplift=uplift,
        db=db,
        fetch_detail=True,
    )
    return {
        "ok": True,
        "mocked": False,
        "item": merged,
        "artifacts_status": merged.get("artifacts_status"),
        "artifacts_available": merged.get("artifacts_available"),
    }


@router.get("/calls/{call_id}/recording")
async def get_call_recording(
    call_id: str,
    db: Database = Depends(get_db),
) -> Any:
    """Serve a locally cached call recording downloaded from Uplift (if any)."""
    call = db.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    path_str = call.get("local_recording_path")
    if path_str:
        path = Path(path_str)
        if path.is_file():
            media = "audio/mpeg"
            if path.suffix == ".wav":
                media = "audio/wav"
            elif path.suffix == ".ogg":
                media = "audio/ogg"
            return FileResponse(path, media_type=media, filename=f"{call_id}-recording{path.suffix}")

    if call.get("recording_url"):
        return {
            "ok": True,
            "available": True,
            "recording_url": call.get("recording_url"),
            "local_cached": False,
            "message": "Recording URL known but not cached locally — open recording_url.",
        }

    raise HTTPException(
        status_code=404,
        detail=(
            "No call recording available yet. Uplift may still be generating it, "
            "or this org's API does not expose recording URLs."
        ),
    )


@router.post("/twilio-webhook")
async def twilio_webhook(
    request: Request,
    uplift: UpliftService = Depends(get_uplift_service),
    db: Database = Depends(get_db),
) -> Response:
    """
    Inbound Twilio number → callback via Uplift outbound (real, not mocked).
    """
    settings = get_settings()
    form = await request.form()
    from_raw = str(form.get("From") or form.get("Caller") or "").strip()
    e164, err = normalize_pakistan_phone(from_raw) if from_raw else (None, "missing From")

    call_result: Dict[str, Any] = {}
    if e164 and uplift.enabled:
        call_result = await uplift.place_call(
            e164,
            additional_instructions=CALL_INSTRUCTIONS
            + " Witness ne Gawah Twilio number par khud dial kiya tha — consent mazboot hai.",
            variables={"participantName": "Witness", "channel": "phone_inbound_callback"},
            idempotency_key=f"twilio-cb-{form.get('CallSid') or e164}",
        )
        if call_result.get("ok"):
            db.upsert_call(
                {
                    "call_id": call_result.get("callId"),
                    "to": e164,
                    "status": "dispatched",
                    "state": call_result.get("status", "dispatched"),
                    "channel": "phone_inbound_callback",
                    "direction": "outbound",
                    "twilio_from": from_raw,
                    "mocked": False,
                    "label": human_label("dispatched"),
                }
            )
            db.record_kpi_event(
                "inbound_callback_placed",
                {"call_id": call_result.get("callId"), "to": e164},
            )

    if call_result.get("ok"):
        say = (
            "Gawah mein khush aamdeed. Aap ka number mil gaya. "
            "Ab hum aap ko Gawah agent se call kar rahe hain. "
            "Yeh line band ho jayegi — please agla call uthaen."
        )
    elif not settings.upliftai_api_key:
        say = (
            "Gawah mein khush aamdeed. Phone calling abhi configure nahi hai. "
            "Dashboard se Call Me option use karein."
        )
    elif err:
        say = (
            "Gawah mein khush aamdeed. Sirf Pakistani mobile numbers support hain. "
            "Dashboard se apna number de kar Call Me dabayen."
        )
    else:
        say = (
            "Gawah mein khush aamdeed. Callback shuru nahi ho saka. "
            "Thori der baad dobara try karein ya dashboard se Call Me use karein."
        )

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="ur-PK">{escape(say)}</Say>
  <Pause length="1"/>
  <Hangup/>
</Response>"""
    return Response(content=twiml, media_type="text/xml")
