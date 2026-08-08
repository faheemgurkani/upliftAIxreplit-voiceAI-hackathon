from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from app.config import get_settings
from app.db.database import Database, get_db
from app.services.call_tracker import (
    ACTIVE_STATES,
    human_label,
    index_remote_sessions,
    merge_uplift_session,
    normalize_call_status,
)
from app.services.phone_utils import CALL_INSTRUCTIONS, normalize_pakistan_phone
from app.services.uplift_service import UpliftService, get_uplift_service

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
    sync: bool = Query(True, description="Refresh status from Uplift sessions"),
    uplift: UpliftService = Depends(get_uplift_service),
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    """Tracked calls with live Uplift status sync for the dashboard."""
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
                    # still allow telephony-marked or toNumber present
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
    for call in local:
        cid = call.get("call_id")
        remote = remote_index.get(str(cid)) if cid else None
        if remote:
            merged = merge_uplift_session(call, remote)
            db.upsert_call(
                {
                    "call_id": cid,
                    "status": merged.get("status"),
                    "state": merged.get("state"),
                    "outcome": merged.get("outcome"),
                    "failure_reason": merged.get("failure_reason"),
                    "connected": merged.get("connected"),
                    "to": merged.get("to"),
                    "from_number": merged.get("from_number"),
                    "label": merged.get("label"),
                    "mocked": False,
                }
            )
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
    }

    return {
        "ok": True,
        "mocked": False,
        "sync_error": sync_error,
        "counts": counts,
        "items": items,
    }


@router.get("/calls/{call_id}")
async def get_phone_call(
    call_id: str,
    uplift: UpliftService = Depends(get_uplift_service),
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    local = db.get_call(call_id)
    remote = await uplift.list_call_sessions(limit=30)
    remote_item = None
    if remote.get("ok"):
        remote_item = index_remote_sessions(remote.get("items") or []).get(call_id)

    if local is None and remote_item is None:
        raise HTTPException(status_code=404, detail="Call not found")

    base = local or {
        "call_id": call_id,
        "to": remote_item.get("toNumber") if remote_item else None,
        "mocked": False,
    }
    if remote_item:
        merged = merge_uplift_session(base, remote_item)
        db.upsert_call(
            {
                "call_id": call_id,
                "status": merged.get("status"),
                "state": merged.get("state"),
                "outcome": merged.get("outcome"),
                "failure_reason": merged.get("failure_reason"),
                "connected": merged.get("connected"),
                "to": merged.get("to"),
                "from_number": merged.get("from_number"),
                "label": merged.get("label"),
                "mocked": False,
            }
        )
        return {"ok": True, "mocked": False, "item": merged}
    return {
        "ok": True,
        "mocked": bool(base.get("mocked", False)),
        "item": {
            **base,
            "label": base.get("label")
            or human_label(base.get("status") or "unknown", base.get("outcome")),
        },
    }


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
