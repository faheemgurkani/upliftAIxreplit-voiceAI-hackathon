"""Google Gemini API — optional LLM provider (does not replace OpenRouter/Groq)."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from app.config import Settings, get_settings


class GeminiService:
    """Gemini Developer API client with JSON and text helpers."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client = None
        self.provider = "gemini"
        self.model = self.settings.gemini_model

        if self.settings.gemini_enabled:
            from google import genai

            self._client = genai.Client(api_key=self.settings.gemini_api_key)

    @property
    def enabled(self) -> bool:
        return self._client is not None

    async def chat_json(
        self,
        prompt: str,
        *,
        system: str = "Reply with valid JSON only.",
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        if self._client is None:
            return {}

        from google.genai import types

        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                response_mime_type="application/json",
            ),
        )
        content = response.text or "{}"
        return self._safe_json(content)

    async def chat_text(self, prompt: str, *, temperature: float = 0.1) -> str:
        if self._client is None:
            return ""

        from google.genai import types

        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature),
        )
        return response.text or ""

    def _safe_json(self, content: str) -> Dict[str, Any]:
        cleaned = content.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(cleaned)
            return parsed if isinstance(parsed, dict) else {"items": parsed}
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}|\[.*\]", cleaned, re.DOTALL)
            if not match:
                return {}
            try:
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, dict) else {"items": parsed}
            except json.JSONDecodeError:
                return {}


_gemini: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    global _gemini
    if _gemini is None:
        _gemini = GeminiService()
    return _gemini
