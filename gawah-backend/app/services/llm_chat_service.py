from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from app.config import Settings, get_settings


class LLMChatService:
    """OpenRouter-first LLM client (OpenAI-compatible). Falls back to Groq if configured."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client = None
        self.provider = "none"
        self.model = ""

        if self.settings.openrouter_enabled:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                base_url=self.settings.openrouter_base_url,
                api_key=self.settings.openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "https://gawah.local",
                    "X-OpenRouter-Title": "Gawah Hackathon",
                },
            )
            self.provider = "openrouter"
            self.model = self.settings.openrouter_model
        elif self.settings.groq_enabled:
            from groq import AsyncGroq

            self._client = AsyncGroq(api_key=self.settings.groq_api_key)
            self.provider = "groq"
            self.model = self.settings.groq_model

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

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        content = response.choices[0].message.content or "{}"
        return self._safe_json(content)

    async def chat_text(self, prompt: str, *, temperature: float = 0.1) -> str:
        if self._client is None:
            return ""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

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


_llm: Optional[LLMChatService] = None


def get_llm_chat_service() -> LLMChatService:
    global _llm
    if _llm is None:
        _llm = LLMChatService()
    return _llm


# Back-compat aliases used by engines
GroqService = LLMChatService


def get_groq_service() -> LLMChatService:
    return get_llm_chat_service()
