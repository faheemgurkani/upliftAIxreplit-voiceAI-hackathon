"""Pakistani phone number helpers for Uplift outbound calling."""

from __future__ import annotations

import re
from typing import Optional, Tuple


def normalize_pakistan_phone(raw: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalize to E.164 (+92…).

    Accepts: +923001234567, 923001234567, 03001234567, 3001234567.
    Returns (e164, error_message).
    """
    if not raw or not str(raw).strip():
        return None, "Phone number is required"

    digits = re.sub(r"[^\d+]", "", str(raw).strip())
    if digits.startswith("+"):
        digits = "+" + re.sub(r"\D", "", digits[1:])
    else:
        digits = re.sub(r"\D", "", digits)

    if digits.startswith("+92"):
        body = digits[3:]
    elif digits.startswith("92") and len(digits) >= 12:
        body = digits[2:]
    elif digits.startswith("0") and len(digits) >= 11:
        body = digits[1:]
    elif len(digits) == 10 and digits.startswith("3"):
        body = digits
    else:
        return None, "Only Pakistani mobile numbers are supported (+92 / 03…)"

    if not re.fullmatch(r"3\d{9}", body):
        return None, "Expected a Pakistani mobile number (10 digits after country code, starting with 3)"

    return f"+92{body}", None


CALL_INSTRUCTIONS = (
    "ROLE: Aap examiner/recorder hain. Line par jo insan hai woh hamesha WITNESS hai. "
    "Aap witness nahi hain — incident aap ne nahi dekha; bayan invent mat karein. "
    "Yeh call Gawah demo / live witness intake hai. "
    "Witness ne khud yeh call request ki hai ya Gawah number par dial kiya hai. "
    "Phase 0 caution (voluntariness + PDPA consent) pehle complete karein, "
    "phir CrPC Section 161 ke mutabiq 5 fields collect karein. "
    "LANGUAGE: Har jumla Urdu (یا Punjabi) Nastaliq script mein bolo — English/Roman Urdu mana. "
    "Witness ki zubaan follow karein."
)

# Prepended onto agent.instructions for adhoc WebRTC sessions (phone uses
# additionalInstructions on POST /calls). Never send this alone via client
# updateInstruction — that REPLACES the full system prompt.
WEB_CALL_INSTRUCTIONS = (
    "ROLE: Aap Gawah system / examiner hain. Browser mein jo user hai woh WITNESS hai. "
    "Kabhi bhi apne aap ko gawah mat samjhein; pehle shakhs mein crime story mat sunayein. "
    "LISTEN FIRST: Witness jo kuch bole — poora suno, interrupt mat karo. "
    "Unke alfaaz se time, jagah, persons, sequence nikaal kar save_witness_statement call karo. "
    "Yeh browser / web call Gawah demo / live witness intake hai — phone call jaisi hi. "
    "Channel: web_browser (WebRTC). Witness mic continuously record ho rahi hai; "
    "hang-up par recording se bhi fields structure hon gi. "
    "LANGUAGE LOCK: Har spoken line اردو نستعلیق میں — never English, never Roman Urdu "
    "(live transcript shows your text). Phase 0 caution pehle, phir free narrative. "
    "Tools: save_witness_statement, flag_inconsistency, flag_intimidation, "
    "enable_privacy_mode, assess_protection_need, confirm_statement. "
    "Readback ke baad 'ہاں' par confirm_statement, phir reference code teen baar."
)
