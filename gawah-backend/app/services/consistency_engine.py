from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.db.database import Database, get_db
from app.models.statement import InconsistencyFlag
from app.services.groq_service import GroqService, get_groq_service


async def segment_into_claims(
    sequence_of_events: str, groq: GroqService
) -> List[str]:
    if groq.enabled:
        result = await groq.chat_json(
            f"""You are a legal evidence analyst. Extract individual factual claims from this witness statement.
Each claim should be a single assertable fact (who, what, when, where, how).
Return ONLY JSON: {{"claims": ["..."]}}
Statement: \"\"\"{sequence_of_events}\"\"\""""
        )
        claims = result.get("claims") or result.get("items") or []
        if isinstance(claims, list) and claims:
            return [str(c).strip() for c in claims if str(c).strip()]

    return [
        s.strip()
        for s in re.split(r"[۔.!?]+", sequence_of_events)
        if len(s.strip()) > 10
    ]


def candidate_pairs(claims: List[str], top_k: int = 5) -> List[Tuple[str, str]]:
    pairs = []
    for i in range(len(claims)):
        for j in range(i + 1, len(claims)):
            words_i = set(claims[i].lower().split())
            words_j = set(claims[j].lower().split())
            intersection = [w for w in words_i if w in words_j and len(w) > 3]
            if len(intersection) >= 2:
                pairs.append((len(intersection), claims[i], claims[j]))
    pairs.sort(key=lambda x: x[0], reverse=True)
    limit = max(top_k, top_k * max(len(claims), 1))
    return [(a, b) for _, a, b in pairs[:limit]]


def heuristic_judge(a: str, b: str) -> Dict[str, Any]:
    """Offline fallback for contradiction cues (edge-case demos without Groq)."""
    la, lb = a.lower(), b.lower()
    night_day = (("raat" in la or "dark" in la or "andhera" in la) and
                 ("din" in lb or "daylight" in lb or "saaf dekha" in lb))
    alone_many = (("akela" in la or "alone" in la) and
                  ("dono" in lb or "two" in lb or "teen" in lb or "four" in lb))
    if night_day:
        return {
            "contradiction": True,
            "reasoning": "Darkness vs clear visual identification",
            "confidence": 0.82,
            "contradiction_type": "temporal",
        }
    if alone_many:
        return {
            "contradiction": True,
            "reasoning": "Alone vs multiple persons present",
            "confidence": 0.75,
            "contradiction_type": "identity",
        }
    return {
        "contradiction": False,
        "reasoning": "no clear contradiction",
        "confidence": 0.1,
        "contradiction_type": "none",
    }


async def llm_contradiction_judge(
    a: str, b: str, groq: GroqService
) -> Dict[str, Any]:
    if not groq.enabled:
        return heuristic_judge(a, b)
    return await groq.chat_json(
        f"""You are a legal analyst assessing witness statement consistency.
Determine if these two statements from the same witness contradict each other.

Statement A: "{a}"
Statement B: "{b}"

Respond ONLY with JSON:
{{"contradiction": true/false, "reasoning": "brief", "confidence": 0.0-1.0,
 "contradiction_type": "temporal|spatial|identity|sequence|sensory|numerical|none"}}"""
    )


def hybrid_score(llm_result: Dict[str, Any], nli_score: float | None = None) -> float:
    confidence = float(llm_result.get("confidence") or 0)
    contradiction = bool(llm_result.get("contradiction"))
    if nli_score is not None:
        llm_label = 1.0 if contradiction else 0.0
        w_llm = confidence / (confidence + abs(nli_score) + 1e-6)
        return w_llm * llm_label + (1 - w_llm) * (1.0 if nli_score > 0.5 else 0.0)
    return confidence if contradiction else 0.0


async def run_consistency_check(
    ref_code: str,
    *,
    db: Database | None = None,
    groq: GroqService | None = None,
) -> List[InconsistencyFlag]:
    """Section 16 Layer 2 — post-call hybrid consistency analysis."""
    db = db or get_db()
    groq = groq or get_groq_service()
    stmt = db.get_statement_by_ref(ref_code)
    if not stmt or not stmt.sequence_of_events:
        return []

    claims = await segment_into_claims(stmt.sequence_of_events, groq)
    pairs = candidate_pairs(claims)
    new_flags: List[InconsistencyFlag] = []

    for claim_a, claim_b in pairs:
        llm_result = await llm_contradiction_judge(claim_a, claim_b, groq)
        score = hybrid_score(llm_result)
        if score > 0.5:
            ctype = llm_result.get("contradiction_type") or "unknown"
            new_flags.append(
                InconsistencyFlag(
                    source="post_call_analysis",
                    contradiction_description=str(llm_result.get("reasoning") or ""),
                    segment_a=claim_a,
                    segment_b=claim_b,
                    contradiction_type=str(ctype),
                    category=str(ctype),
                    hybrid_score=score,
                    score=score,
                    analysis=str(llm_result.get("reasoning") or ""),
                    legal_risk="Defence may use this for CrPC 162 cross-examination.",
                    flagged_at=datetime.now(timezone.utc).isoformat(),
                )
            )

    if new_flags:
        existing = list(stmt.inconsistency_flags or [])
        existing.extend(new_flags)
        stmt.inconsistency_flags = existing
        if stmt.status not in {"urgent_escalation", "incomplete"}:
            stmt.status = "pending_review"
        db.save_statement(stmt)
        db.record_kpi_event(
            "consistency_flags_added",
            {"ref_code": ref_code, "count": len(new_flags)},
        )
    return new_flags
