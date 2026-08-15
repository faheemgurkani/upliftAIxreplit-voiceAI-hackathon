"""Google Cloud Text-to-Speech — optional TTS provider (does not replace Uplift TTS)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.config import Settings, get_settings


class GoogleTTSService:
    """Synthesize Urdu readback audio via Google Cloud Text-to-Speech."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client = None

        if self.settings.google_cloud_enabled:
            from google.cloud import texttospeech_v1 as tts

            self._client = tts.TextToSpeechAsyncClient()

    @property
    def enabled(self) -> bool:
        return self._client is not None

    async def synthesize_speech(
        self,
        text: str,
        *,
        language_code: Optional[str] = None,
        voice_name: Optional[str] = None,
    ) -> bytes:
        if not self.enabled or not text.strip():
            return b""

        from google.cloud import texttospeech_v1 as tts

        lang = language_code or self.settings.google_tts_language_code
        voice_params: Dict[str, Any] = {"language_code": lang}
        resolved_voice = voice_name or self.settings.google_tts_voice_name
        if resolved_voice:
            voice_params["name"] = resolved_voice

        request = tts.SynthesizeSpeechRequest(
            input=tts.SynthesisInput(text=text),
            voice=tts.VoiceSelectionParams(**voice_params),
            audio_config=tts.AudioConfig(
                audio_encoding=tts.AudioEncoding.MP3,
                speaking_rate=self.settings.google_tts_speaking_rate,
            ),
        )
        response = await self._client.synthesize_speech(request=request)
        return bytes(response.audio_content or b"")

    async def synthesize_result(
        self,
        text: str,
        *,
        language_code: Optional[str] = None,
        voice_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "ok": False,
                "detail": "Google Cloud TTS not configured (set GOOGLE_APPLICATION_CREDENTIALS)",
                "provider": "google_tts",
            }
        try:
            audio = await self.synthesize_speech(
                text,
                language_code=language_code,
                voice_name=voice_name,
            )
            return {
                "ok": bool(audio),
                "audio_bytes": len(audio),
                "provider": "google_tts",
                "language_code": language_code or self.settings.google_tts_language_code,
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "detail": str(exc), "provider": "google_tts"}


_tts: Optional[GoogleTTSService] = None


def get_google_tts_service() -> GoogleTTSService:
    global _tts
    if _tts is None:
        _tts = GoogleTTSService()
    return _tts
