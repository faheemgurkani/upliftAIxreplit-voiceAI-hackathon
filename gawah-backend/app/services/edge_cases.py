from __future__ import annotations

from typing import Any, Dict, Optional

# Spec §10 — edge-case handling helpers used by tool routers / agent responses.

INTIMIDATION_TRIGGERS = [
    "mujhe daraya",
    "dhamki",
    "main darta",
    "main darti",
    "nahi aana chahiye",
    "agar unhein pata",
    "ghar wale nahi",
    "paisa diya",
    "samjhota",
]

ACTIVE_THREAT_RESPONSE = (
    "Agar aap ko abhi khatra hai — 15 (Rescue), 1122 (Rescue Punjab), "
    "ya 1715 (Police) par call karein."
)

JOINT_STATEMENT_REFUSAL = (
    "Aap ka bayan alag se darz hoga — main aap ko alag reference code dunga. "
    "Joint statements qanoonan ghalat hain."
)

COUNTER_STATEMENT_REFUSAL = (
    "Yeh system gawahon ke liye hai. Aap lawyer se raabta karein."
)

THUMBPRINT_REFUSAL = (
    "Aap ki awaaz hi aap ki tasdeeq hai — koi signature nahi chahiye."
)

PASHTO_LIMITATION = (
    "Mujhe khed hai, abhi Pashto mein meri samajh limited hai."
)


def detect_intimidation_text(text: str) -> bool:
    lower = text.lower()
    return any(t in lower for t in INTIMIDATION_TRIGGERS)


def handle_language(language: str) -> Dict[str, Any]:
    if language == "ps":
        return {
            "supported": False,
            "presentationInstructions": PASHTO_LIMITATION,
        }
    return {"supported": True, "presentationInstructions": ""}


def handle_delay_days(days: Optional[int]) -> Dict[str, Any]:
    if days is None:
        return {"ask_reason": False, "high_risk": False}
    return {
        "ask_reason": days > 1,
        "high_risk": days > 30,
        "prompt": "Itne dino baad bayan dene ki kya wajah hai?" if days > 30 else None,
    }


def handle_mid_call_disconnect(phase: str) -> Dict[str, Any]:
    return {
        "status": "incomplete",
        "call_phase_at_disconnect": phase,
        "preserve_partial": True,
    }


def handle_callback_lookup_allowed_fields() -> list[str]:
    """Unverified callback must not read full statement."""
    return ["ref_code", "status", "created_at", "location", "time_of_incident"]
