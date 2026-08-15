"""Google Cloud Speech-to-Text — optional STT provider (does not replace Uplift STT)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from app.config import Settings, get_settings


def _audio_encoding_for_filename(filename: str) -> int:
    from google.cloud import speech_v1 as speech

    ext = Path(filename).suffix.lower()
    mapping = {
        ".wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        ".flac": speech.RecognitionConfig.AudioEncoding.FLAC,
        ".mp3": speech.RecognitionConfig.AudioEncoding.MP3,
        ".mpeg": speech.RecognitionConfig.AudioEncoding.MP3,
        ".ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        ".webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        ".opus": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
    }
    return mapping.get(ext, speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED)


class GoogleSTTService:
    """Transcribe witness audio via Google Cloud Speech-to-Text."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.google_cloud_enabled

    async def transcribe(
        self,
        file_bytes: bytes,
        filename: str = "recording.mp3",
        *,
        language_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "ok": False,
                "transcript": "",
                "detail": "Google Cloud STT not configured (set GOOGLE_APPLICATION_CREDENTIALS)",
                "provider": "google_stt",
            }

        import asyncio

        from google.cloud import speech_v1 as speech

        lang = language_code or self.settings.google_stt_language_code
        encoding = _audio_encoding_for_filename(filename)

        def _recognize() -> Dict[str, Any]:
            client = speech.SpeechClient()
            audio = speech.RecognitionAudio(content=file_bytes)
            config = speech.RecognitionConfig(
                encoding=encoding,
                language_code=lang,
                enable_automatic_punctuation=True,
            )
            response = client.recognize(config=config, audio=audio)
            parts = []
            for result in response.results:
                alt = result.alternatives[0] if result.alternatives else None
                if alt and alt.transcript:
                    parts.append(alt.transcript.strip())
            transcript = " ".join(parts).strip()
            return {
                "ok": bool(transcript),
                "transcript": transcript,
                "provider": "google_stt",
                "language_code": lang,
                "raw": {"result_count": len(response.results)},
            }

        try:
            return await asyncio.to_thread(_recognize)
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "transcript": "",
                "detail": str(exc),
                "provider": "google_stt",
            }


_stt: Optional[GoogleSTTService] = None


def get_google_stt_service() -> GoogleSTTService:
    global _stt
    if _stt is None:
        _stt = GoogleSTTService()
    return _stt
