from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from app.config import Settings, get_settings
from app.models.statement import StructuredStatement

STRUCTURE_PROMPT = """
You are a legal statement assistant for Pakistan's criminal justice system.
Given a raw witness account in {language}, extract and return JSON with:
- incident_date
- incident_time
- incident_location
- persons_involved (list of strings)
- sequence_of_events (ordered list of strings)
- witness_name
- inconsistencies (list any contradictions in the account)

Raw account:
{transcript}

Return ONLY valid JSON. No explanation.
""".strip()

INCONSISTENCY_PROMPT = """
Review this witness account for internal contradictions, timeline gaps, or unclear facts.
Return JSON: {{"inconsistencies": ["..."]}}

Account:
{transcript}
""".strip()


class LLMService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._client = None
        if self.settings.llm_enabled:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    async def structure_statement(self, transcript: str, language: str) -> StructuredStatement:
        if not transcript.strip():
            return StructuredStatement()

        if self._client is None:
            return self._heuristic_structure(transcript)

        prompt = STRUCTURE_PROMPT.format(language=language, transcript=transcript)
        response = await self._client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured legal witness statements. Reply with JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        data = self._safe_json(content)
        return StructuredStatement.model_validate(data)

    async def flag_inconsistencies(self, transcript: str) -> List[str]:
        if not transcript.strip():
            return []

        if self._client is None:
            return self._heuristic_inconsistencies(transcript)

        prompt = INCONSISTENCY_PROMPT.format(transcript=transcript)
        response = await self._client.chat.completions.create(
            model=self.settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You flag inconsistencies in witness accounts. Reply with JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content or "{}"
        data = self._safe_json(content)
        items = data.get("inconsistencies", [])
        return [str(item) for item in items if item]

    def _safe_json(self, content: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                return {}
            try:
                parsed = json.loads(match.group(0))
                return parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {}

    def _heuristic_structure(self, transcript: str) -> StructuredStatement:
        """Offline/demo fallback when OPENAI_API_KEY is not set."""
        sentences = [
            s.strip()
            for s in re.split(r"[.!?؟\n]+", transcript)
            if s.strip()
        ]
        persons = sorted(
            {
                token.strip(" ,.")
                for token in re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b", transcript)
            }
        )
        return StructuredStatement(
            incident_date="unknown",
            incident_time="unknown",
            incident_location="unknown",
            persons_involved=persons[:8],
            sequence_of_events=sentences[:12] or [transcript.strip()],
            witness_name=persons[0] if persons else "unknown",
            inconsistencies=self._heuristic_inconsistencies(transcript),
        )

    def _heuristic_inconsistencies(self, transcript: str) -> List[str]:
        flags: List[str] = []
        lower = transcript.lower()
        if "maybe" in lower or "not sure" in lower or "شاید" in transcript:
            flags.append("Witness expressed uncertainty in parts of the account.")
        if len(transcript.split()) < 20:
            flags.append("Account is very short; may be incomplete.")
        day_words = ["morning", "afternoon", "night", "صبح", "شام", "رات"]
        mentioned = [w for w in day_words if w in lower or w in transcript]
        if len(mentioned) >= 2:
            flags.append("Multiple time-of-day references detected; verify timeline.")
        return flags


_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
