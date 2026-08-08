from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from app.config import Settings, get_settings
from app.prompts.agent_config import GAWAH_ASSISTANT_CONFIG


class UpliftService:
    """
    Uplift AI integration (Singapore region for Pakistan).

    - Realtime Assistants: create / reuse assistant, createSession
    - TTS REST: statement readback audio
    - STT REST: admin transcription
    - Outbound calls: POST /calls (Singapore only)
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.uplift_enabled

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.upliftai_api_key}",
            "Content-Type": "application/json",
        }

    async def ensure_assistant(self) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "ok": False,
                "assistantId": self.settings.uplift_assistant_id or "demo-assistant",
                "detail": "UPLIFTAI_API_KEY not set",
            }
        if self.settings.uplift_assistant_id:
            return {"ok": True, "assistantId": self.settings.uplift_assistant_id}

        url = f"{self.settings.uplift_base_url.rstrip('/')}/realtime-assistants"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json=GAWAH_ASSISTANT_CONFIG,
            )
            if response.status_code >= 400:
                return {
                    "ok": False,
                    "detail": response.text,
                    "status_code": response.status_code,
                }
            data = response.json()
            assistant_id = (
                data.get("realtimeAssistantId")
                or data.get("assistantId")
                or data.get("id")
            )
            return {"ok": True, "assistantId": assistant_id, "raw": data}

    async def create_session(
        self, participant_name: str = "Witness"
    ) -> Dict[str, Any]:
        assistant = await self.ensure_assistant()
        assistant_id = assistant.get("assistantId") or self.settings.uplift_assistant_id

        if not self.enabled or not assistant_id or str(assistant_id).startswith("demo"):
            # Offline demo session so frontend can proceed
            return {
                "ok": True,
                "demo": True,
                "token": "demo-session-token",
                "wsUrl": "wss://demo.local/gawah",
                "roomName": f"gawah-demo-{participant_name.replace(' ', '-').lower()}",
                "assistantId": assistant_id or "demo-assistant",
            }

        url = (
            f"{self.settings.uplift_base_url.rstrip('/')}"
            f"/realtime-assistants/{assistant_id}/createSession"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json={"participantName": participant_name},
            )
            if response.status_code >= 400:
                return {
                    "ok": False,
                    "detail": response.text,
                    "status_code": response.status_code,
                }
            data = response.json()
            return {
                "ok": True,
                "demo": False,
                "token": data.get("token") or data.get("accessToken"),
                "wsUrl": data.get("wsUrl") or data.get("serverUrl") or data.get("url"),
                "roomName": data.get("roomName") or data.get("room"),
                "assistantId": assistant_id,
                "raw": data,
            }

    async def synthesize_speech(self, text: str) -> bytes:
        if not self.enabled:
            return b""

        url = f"{self.settings.uplift_base_url.rstrip('/')}/synthesis/text-to-speech"
        # Prefer stream endpoint if binary response expected
        payload = {
            "voiceId": self.settings.uplift_tts_voice_id,
            "text": text[:10000],
            "outputFormat": self.settings.uplift_tts_output_format,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
            if response.status_code >= 400:
                # Fallback to stream endpoint
                stream_url = (
                    f"{self.settings.uplift_base_url.rstrip('/')}"
                    "/synthesis/text-to-speech/stream"
                )
                response = await client.post(
                    stream_url, headers=self._headers(), json=payload
                )
            response.raise_for_status()
            return response.content

    async def store_readback_audio(self, ref_code: str, text: str) -> Optional[str]:
        audio = await self.synthesize_speech(text)
        if not audio:
            return None

        path = Path(self.settings.local_audio_dir) / ref_code
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / "readback.mp3"
        file_path.write_bytes(audio)

        # Supabase storage upload when configured
        if self.settings.use_supabase:
            try:
                from supabase import create_client

                client = create_client(
                    self.settings.supabase_url,
                    self.settings.supabase_anon_or_service_key,
                )
                client.storage.from_("statements").upload(
                    f"{ref_code}/readback.mp3",
                    audio,
                    {"content-type": "audio/mpeg", "upsert": "true"},
                )
                return f"statements/{ref_code}/readback.mp3"
            except Exception:
                pass

        return str(file_path)

    async def transcribe(self, file_bytes: bytes, filename: str = "recording.mp3") -> Dict[str, Any]:
        if not self.enabled:
            return {"ok": False, "transcript": "", "detail": "Uplift key missing"}

        url = f"{self.settings.uplift_base_url.rstrip('/')}/transcribe/speech-to-text"
        headers = {"Authorization": f"Bearer {self.settings.upliftai_api_key}"}
        files = {"file": (filename, file_bytes, "audio/mpeg")}
        data = {"model": "scribe", "language": "ur"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, files=files, data=data)
            if response.status_code >= 400:
                return {"ok": False, "detail": response.text}
            payload = response.json()
            return {
                "ok": True,
                "transcript": payload.get("text") or payload.get("transcript") or "",
                "raw": payload,
            }

    async def place_call(
        self,
        to: str,
        *,
        additional_instructions: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        assistant = await self.ensure_assistant()
        assistant_id = assistant.get("assistantId") or self.settings.uplift_assistant_id
        if not self.enabled or not assistant_id:
            return {
                "ok": False,
                "detail": (
                    "Uplift calling not configured. Set UPLIFTAI_API_KEY and "
                    "UPLIFT_BASE_URL=https://ap-southeast-1.api.upliftai.org/v1"
                ),
            }

        url = f"{self.settings.uplift_base_url.rstrip('/')}/calls"
        headers = self._headers()
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key[:256]
        body: Dict[str, Any] = {"assistantId": assistant_id, "to": to}
        if additional_instructions:
            body["additionalInstructions"] = additional_instructions[:2000]
        if variables:
            body["variables"] = variables

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=body)
                if response.status_code >= 400:
                    return {
                        "ok": False,
                        "status_code": response.status_code,
                        "detail": response.text,
                    }
                data = response.json()
                return {
                    "ok": True,
                    "callId": data.get("callId") or data.get("id"),
                    "status": data.get("status", "dispatched"),
                    "assistantId": assistant_id,
                    "to": to,
                    "raw": data,
                }
        except httpx.HTTPError as exc:
            return {"ok": False, "status_code": 502, "detail": f"Uplift call request failed: {exc}"}

    async def list_call_sessions(self, *, limit: int = 10) -> Dict[str, Any]:
        """Poll recent realtime-assistant sessions (includes outbound call states)."""
        assistant = await self.ensure_assistant()
        assistant_id = assistant.get("assistantId") or self.settings.uplift_assistant_id
        if not self.enabled or not assistant_id:
            return {"ok": False, "items": [], "detail": "Uplift not configured"}

        limit = max(1, min(limit, 50))
        url = (
            f"{self.settings.uplift_base_url.rstrip('/')}"
            f"/realtime-assistants/{assistant_id}/sessions"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers=self._headers(),
                params={"limit": limit},
            )
            if response.status_code >= 400:
                return {
                    "ok": False,
                    "items": [],
                    "status_code": response.status_code,
                    "detail": response.text,
                }
            data = response.json()
            items = data if isinstance(data, list) else data.get("sessions") or data.get("items") or []
            return {"ok": True, "assistantId": assistant_id, "items": items, "raw": data}


_uplift: UpliftService | None = None


def get_uplift_service() -> UpliftService:
    global _uplift
    if _uplift is None:
        _uplift = UpliftService()
    return _uplift
