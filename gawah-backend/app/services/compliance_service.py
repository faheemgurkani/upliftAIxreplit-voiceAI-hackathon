"""
Compliance helpers — FUTURE WORK / NOT ACTIVE IN MVP.

See docs/COMPLIANCE_FUTURE_WORK.md for the full map:

- CrPC 1898 §§161–162 (criminal procedure)
- Personal Data Protection Bill 2023 / forthcoming PDPA (privacy readiness)
- PTA / PECA consent & anti-spam (phone channel)
- National AI Policy 2025 (soft AI governance)

Do not claim statutory PDPA compliance until Pakistan enacts the law.
"""

from __future__ import annotations

from typing import Any, Dict


COMPLIANCE_TARGETS = {
    "criminal_procedure": {
        "instrument": "Code of Criminal Procedure, 1898",
        "focus": ["section_161", "section_162"],
        "watch": "Criminal Procedure Amendment Bill 2025/2026",
        "status": "binding_context_for_product_claims",
    },
    "personal_data": {
        "instrument": "Personal Data Protection Bill, 2023",
        "alias_drafts": ["Personal Data Protection Act 2025 (MoITT update track)"],
        "international_baseline": "EU GDPR (readiness only)",
        "status": "future_integration_draft_not_enacted_as_of_2026-08",
    },
    "telecom": {
        "instrument": "PTA unsolicited/spam framework + PECA 2016 spam provisions",
        "status": "future_integration_for_outbound_pstn",
    },
    "ai_policy": {
        "instrument": "National AI Policy 2025",
        "status": "soft_guidance_only",
    },
}


def compliance_status_banner() -> Dict[str, Any]:
    """Expose a non-binding readiness banner for /health or docs UIs later."""
    return {
        "mvp_claims_pdpa_compliant": False,
        "future_work": True,
        "targets": COMPLIANCE_TARGETS,
        "doc": "docs/COMPLIANCE_FUTURE_WORK.md",
    }


def record_consent_artifact(*_args, **_kwargs) -> Dict[str, Any]:
    """Placeholder: store Phase-0 voluntariness consent evidence."""
    return {
        "ok": False,
        "implemented": False,
        "detail": "Future work — see docs/COMPLIANCE_FUTURE_WORK.md",
    }


def schedule_retention_deletion(*_args, **_kwargs) -> Dict[str, Any]:
    """Placeholder: retention clock for audio/transcripts."""
    return {
        "ok": False,
        "implemented": False,
        "detail": "Future work — see docs/COMPLIANCE_FUTURE_WORK.md",
    }
