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
    "Yeh call Gawah demo / live witness intake hai. "
    "Witness ne khud yeh call request ki hai ya Gawah number par dial kiya hai. "
    "Phase 0 caution (voluntariness + PDPA consent) pehle complete karein, "
    "phir CrPC Section 161 ke mutabiq 5 fields collect karein. "
    "Hamesha Urdu ya Punjabi mein baat karein — witness ki zubaan follow karein."
)

# Injected on web WebRTC connect via updateInstruction — mirrors phone CALL_INSTRUCTIONS.
WEB_CALL_INSTRUCTIONS = (
    "Yeh browser / web call Gawah demo / live witness intake hai — phone call jaisi hi. "
    "Channel: web_browser (WebRTC). Witness ne khud demo se session shuru kiya hai. "
    "Phase 0 caution (voluntariness + PDPA consent) pehle complete karein, "
    "phir CrPC Section 161 ke mutabiq 5 fields collect karein. "
    "Hamesha Urdu ya Punjabi mein baat karein — witness ki zubaan follow karein. "
    "Tools available: save_witness_statement, flag_inconsistency, flag_intimidation, "
    "enable_privacy_mode, assess_protection_need, confirm_statement. "
    "Readback ke baad jab witness 'haan' kahe to confirm_statement call karein, "
    "phir reference code teen baar bolen."
)
