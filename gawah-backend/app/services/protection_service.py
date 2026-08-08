from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.config import get_settings
from app.models.statement import StatementRecord

PROTECTION_ACTS = {
    "Punjab": "Punjab Witness Protection Act 2018 — Unit II (Serious Offences)",
    "Sindh": "Sindh Witness Protection Act 2013",
    "Balochistan": "Balochistan Witness Protection Act 2016",
    "KPK": "Federal Witness Protection, Security and Benefit Act 2017",
    "Federal": "Federal Witness Protection, Security and Benefit Act 2017",
    "unknown": "Federal Witness Protection, Security and Benefit Act 2017",
}


def resolve_protection_act(province: str, offence_type: str) -> str:
    if offence_type == "terrorism" and province == "Punjab":
        return "Punjab Witness Protection Act 2018 — Unit I (Terrorism)"
    return PROTECTION_ACTS.get(province, PROTECTION_ACTS["Federal"])


def qualifies_for_protection(
    offence_type: str,
    *,
    witness_is_victim: bool = False,
    witness_appears_under_16: bool = False,
    intimidation_already_flagged: bool = False,
) -> bool:
    return (
        offence_type in {"terrorism", "sexual_offence", "murder", "kidnapping"}
        or witness_appears_under_16
        or intimidation_already_flagged
        or witness_is_victim
    )


def assess_protection(
    *,
    offence_type: str,
    witness_is_victim: bool = False,
    witness_appears_under_16: bool = False,
    intimidation_already_flagged: bool = False,
    province: str = "unknown",
) -> Dict[str, Any]:
    act = resolve_protection_act(province, offence_type)
    qualifies = qualifies_for_protection(
        offence_type,
        witness_is_victim=witness_is_victim,
        witness_appears_under_16=witness_appears_under_16,
        intimidation_already_flagged=intimidation_already_flagged,
    )
    grounds = []
    if intimidation_already_flagged:
        grounds.append("Intimidation / threat indicated")
    if witness_is_victim:
        grounds.append("Witness is victim")
    if witness_appears_under_16:
        grounds.append("Witness appears under 16")
    grounds.append(f"Offence category: {offence_type}")

    presentation = ""
    if qualifies:
        presentation = (
            "Main aap ko ek zaruri baat batana chahta hoon: Pakistan ka qanoon aap ki "
            "hifazat ka intezam karta hai. Agar aap chahein to hum ek darkhwast tayyar "
            f"kar sakte hain jo {act} ke tehat aap ko tahaffuz de sakta hai. Kya aap "
            "chahte hain ke hum aap ke case ke NGO partner ko yeh darkhwast bhejen?"
        )
    return {
        "qualifies": qualifies,
        "applicable_act": act if qualifies else None,
        "grounds": grounds if qualifies else [],
        "province": province,
        "presentationInstructions": presentation,
    }


def generate_protection_referral_pdf(stmt: StatementRecord, act: str) -> str:
    settings = get_settings()
    out_dir = Path(settings.local_audio_dir) / stmt.ref_code
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "protection_referral.pdf"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("GAWAH — Witness Protection Referral", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Reference Code: {stmt.ref_code}", styles["Normal"]),
        Paragraph(f"Applicable Act: {act}", styles["Normal"]),
        Paragraph(f"Offence Category: {stmt.offence_category or 'n/a'}", styles["Normal"]),
        Paragraph(f"Location: {stmt.location}", styles["Normal"]),
        Paragraph(
            f"Intimidation Flag: {'Yes' if stmt.intimidation_flag else 'No'}",
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph(
            "This referral is generated for NGO / protection-unit review. "
            "It is not a court order.",
            styles["Italic"],
        ),
    ]
    doc.build(story)
    path.write_bytes(buffer.getvalue())
    return str(path)
