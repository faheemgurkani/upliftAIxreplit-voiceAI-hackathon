from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.models.statement import StructuredStatement

READBACK_TEMPLATES = {
    "urdu": (
        "براہ کرم تصدیق کریں۔ آپ نے بتایا کہ واقعہ {incident_date} کو "
        "{incident_time} بجے {incident_location} پر پیش آیا۔ "
        "شامل افراد: {persons}. واقعات کی ترتیب: {events}. "
        "اگر یہ درست ہے تو ہاں کہیں، ورنہ درست کریں۔"
    ),
    "punjabi": (
        "براہ مہربانی تصدیق کرو۔ تسیں دسیا کہ واقعہ {incident_date} نوں "
        "{incident_time} ویلے {incident_location} تے ہویا۔ "
        "لوک شامل: {persons}. واقعات: {events}. "
        "اگر ٹھیک اے تے ہاں آکھو، نہیں تے درست کرو۔"
    ),
    "pashto": (
        "مهرباني وکړئ تایید کړئ. تاسو وویل چې پیښه په {incident_date} "
        "په {incident_time} کې په {incident_location} کې وشوه. "
        "شامل کسان: {persons}. ترتیب: {events}. "
        "که سم وي نو هو ووایاست، که نه نو سم یې کړئ."
    ),
    "english": (
        "Please confirm. You said the incident occurred on {incident_date} "
        "at {incident_time} in {incident_location}. "
        "Persons involved: {persons}. Sequence of events: {events}. "
        "Say yes if this is correct, or correct any mistakes."
    ),
}


def generate_case_id(station_id: Optional[str] = None) -> str:
    """Generate a short human-usable case reference code."""
    settings = get_settings()
    stamp = datetime.now(timezone.utc).strftime("%y%m%d")
    station = (station_id or "GEN").upper().replace(" ", "")[:4]
    nonce = secrets.token_hex(2).upper()
    digest = hashlib.sha256(
        f"{settings.case_id_secret}:{stamp}:{station}:{nonce}".encode("utf-8")
    ).hexdigest()[:4].upper()
    return f"GW-{station}-{stamp}-{nonce}{digest}"


def generate_readback_text(
    structured: StructuredStatement | dict,
    language: str = "urdu",
) -> str:
    if isinstance(structured, dict):
        structured = StructuredStatement.model_validate(structured)

    template = READBACK_TEMPLATES.get(language, READBACK_TEMPLATES["urdu"])
    persons = ", ".join(structured.persons_involved) or "unknown"
    events = "; ".join(structured.sequence_of_events[:5]) or "not specified"

    return template.format(
        incident_date=structured.incident_date or "unknown",
        incident_time=structured.incident_time or "unknown",
        incident_location=structured.incident_location or "unknown",
        persons=persons,
        events=events,
    )


def spoken_case_status(case_id: str, status: str, title: Optional[str] = None) -> str:
    title_bit = f" titled {title}" if title else ""
    mapping = {
        "open": f"Case {case_id}{title_bit} is open and awaiting investigation.",
        "in_progress": f"Case {case_id}{title_bit} is currently in progress.",
        "statement_pending": (
            f"Case {case_id}{title_bit} is awaiting witness statement confirmation."
        ),
        "closed": f"Case {case_id}{title_bit} is closed.",
    }
    return mapping.get(status, f"Case {case_id} status is {status}.")


def merge_structured(
    base: StructuredStatement,
    incoming: StructuredStatement,
) -> StructuredStatement:
    data = base.model_dump()
    new = incoming.model_dump()
    for key, value in new.items():
        if value in ("", None, [], {}):
            continue
        data[key] = value
    return StructuredStatement.model_validate(data)
