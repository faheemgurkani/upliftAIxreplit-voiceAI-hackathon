from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

import httpx

from app.config import get_settings


async def notify_ngo(event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    settings = get_settings()
    body = {
        "type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    if not settings.ngo_webhook_url:
        return {"ok": False, "skipped": True, "body": body}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(settings.ngo_webhook_url, json=body)
        return {
            "ok": response.status_code < 400,
            "status_code": response.status_code,
            "body": body,
        }
