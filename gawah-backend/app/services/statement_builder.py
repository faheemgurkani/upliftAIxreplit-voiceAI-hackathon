from __future__ import annotations

import secrets
from typing import Any, Dict, List, Optional

from app.models.statement import SaveStatementArgs, StatementRecord


REF_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_ref_code(length: int = 6) -> str:
    return "".join(secrets.choice(REF_CHARS) for _ in range(length))


def build_readback_text(fields: SaveStatementArgs | Dict[str, Any] | StatementRecord) -> str:
    if isinstance(fields, StatementRecord):
        data = {
            "time_of_incident": fields.time_of_incident,
            "location": fields.location,
            "persons_present": fields.persons_present,
            "sequence_of_events": fields.sequence_of_events,
            "relationship_to_accused": fields.relationship_to_accused,
        }
    elif isinstance(fields, SaveStatementArgs):
        data = fields.model_dump()
    else:
        data = fields

    parts: List[str] = []
    if data.get("time_of_incident"):
        parts.append(f"Waqia: {data['time_of_incident']} ko hua.")
    if data.get("location"):
        parts.append(f"Jagah: {data['location']}.")
    persons = data.get("persons_present") or []
    if isinstance(persons, str):
        persons = [persons]
    if persons:
        parts.append(f"Maujood afraad: {', '.join(persons)}.")
    if data.get("sequence_of_events"):
        seq = data["sequence_of_events"]
        if isinstance(seq, list):
            seq = " ".join(seq)
        parts.append(f"Waqiat: {seq}")
    if data.get("relationship_to_accused"):
        parts.append(f"Mulzim se taluq: {data['relationship_to_accused']}.")
    return "\n".join(parts)


def spoken_status_for_callback(stmt: StatementRecord) -> str:
    """Limited callback disclosure — location + date only, no full statement."""
    when = stmt.time_of_incident or stmt.created_at
    return (
        f"Reference {stmt.ref_code}. Status: {stmt.status}. "
        f"Location on record: {stmt.location or 'not set'}. "
        f"Incident time on record: {when}."
    )


def delay_flags(days: Optional[int]) -> Dict[str, Any]:
    if days is None:
        return {"delayed_statement_high_risk": False}
    return {
        "statement_delay_days": days,
        "delayed_statement_high_risk": days > 30,
    }
