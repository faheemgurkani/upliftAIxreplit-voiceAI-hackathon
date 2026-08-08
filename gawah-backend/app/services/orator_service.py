from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from app.config import Settings, get_settings


class OratorService:
    """
    Uplift AI Orator integration helper.

    In the Vapi + Orator pipeline, Vapi typically delivers already-transcribed
    text to our webhooks. This service is available for direct Orator calls
    (e.g. offline re-processing or custom STT/TTS hooks).
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.uplift_orator_key)

    async def transcribe_audio(
        self,
        *,
        audio_url: Optional[str] = None,
        language: str = "urdu",
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "ok": False,
                "provider": "orator",
                "transcript": "",
                "detail": "UPLIFT_ORATOR_KEY not configured; expecting transcript from Vapi webhook.",
            }

        payload = {"language": language}
        if audio_url:
            payload["audio_url"] = audio_url

        headers = {
            "Authorization": f"Bearer {self.settings.uplift_orator_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.settings.uplift_orator_base_url.rstrip('/')}/orator/transcribe"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code >= 400:
                return {
                    "ok": False,
                    "provider": "orator",
                    "transcript": "",
                    "detail": response.text,
                    "status_code": response.status_code,
                }
            data = response.json()
            return {
                "ok": True,
                "provider": "orator",
                "transcript": data.get("transcript") or data.get("text") or "",
                "raw": data,
            }

    async def synthesize_speech(
        self,
        text: str,
        *,
        language: str = "urdu",
        voice: str = "default",
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "ok": False,
                "provider": "orator",
                "audio_url": None,
                "detail": "UPLIFT_ORATOR_KEY not configured; Vapi/TTS handles readback in MVP.",
            }

        headers = {
            "Authorization": f"Bearer {self.settings.uplift_orator_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.settings.uplift_orator_base_url.rstrip('/')}/orator/tts"
        payload = {"text": text, "language": language, "voice": voice}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code >= 400:
                return {
                    "ok": False,
                    "provider": "orator",
                    "audio_url": None,
                    "detail": response.text,
                    "status_code": response.status_code,
                }
            data = response.json()
            return {
                "ok": True,
                "provider": "orator",
                "audio_url": data.get("audio_url") or data.get("url"),
                "raw": data,
            }


_orator_service: OratorService | None = None


def get_orator_service() -> OratorService:
    global _orator_service
    if _orator_service is None:
        _orator_service = OratorService()
    return _orator_service
