from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from app.db.database import Database, get_db
from app.services.uplift_service import UpliftService, get_uplift_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionCreateBody(BaseModel):
    participantName: str = Field(default="Witness", alias="participantName")
    participant_name: Optional[str] = None

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
        }
    )
    db.record_kpi_event("session_created", {"room": session.get("roomName")})
    # Normalize keys for frontend
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
    }


@router.post("/twilio-webhook")
async def twilio_webhook() -> Response:
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="ur-PK">Gawah mein khush aamdeed. Aap ka connection ho raha hai.</Say>
  <Connect>
    <Stream url="wss://your-bridge-server.com/twilio-to-webrtc" />
  </Connect>
</Response>"""
    return Response(content=twiml, media_type="text/xml")
