from __future__ import annotations

from typing import Any, Dict, List

from app.db.database import Database, get_db

# KPIs / ROI proxies derived from the problem statement + edge-case coverage.
# These measure hackathon demo impact readiness for judges/NGOs.

KPI_DEFINITIONS = {
    "statements_captured": "Total witness statements stored (voice-first intake)",
    "witness_confirmed": "Statements with spoken confirmation (informed consent)",
    "urgent_escalations": "Intimidation / protection escalations",
    "inconsistency_flagged": "Statements with ≥1 inconsistency flag (CrPC 162 risk surface)",
    "privacy_mode_uses": "Anonymous / privacy-mode sessions",
    "protection_referrals": "Witness protection referrals generated",
    "multi_witness_clusters": "Incident clusters with ≥2 statements",
    "incomplete_calls": "Mid-call disconnects preserved as incomplete",
    "delayed_high_risk": "Statements delayed >30 days (credibility risk)",
    "punjabi_or_urdu_calls": "Calls in Urdu/Punjabi (language access ROI)",
}


def compute_kpis(db: Database | None = None) -> Dict[str, Any]:
    db = db or get_db()
    statements, total = db.list_statements(page=1, page_size=1000)
    clusters = db.list_clusters()

    pending = sum(1 for s in statements if s.status == "pending_review")
    urgent = sum(1 for s in statements if s.status == "urgent_escalation")
    confirmed = sum(1 for s in statements if s.confirmed_by_witness)
    with_flags = sum(1 for s in statements if s.inconsistency_flags)
    privacy = sum(1 for s in statements if s.privacy_mode)
    protection = sum(1 for s in statements if s.protection_referral_generated)
    incomplete = sum(1 for s in statements if s.status == "incomplete")
    delayed = sum(1 for s in statements if s.delayed_statement_high_risk)
    lang_access = sum(
        1 for s in statements if s.language_of_call in {"ur", "pa", "mixed"}
    )
    multi = sum(1 for c in clusters if (c.statement_count or 0) >= 2)

    scores = [s.corroboration_score for s in statements if s.corroboration_score is not None]
    avg_corr = round(sum(scores) / len(scores), 3) if scores else None

    # ROI proxies for judges (directional, not financial)
    roi = {
        "literacy_barrier_removed": total,  # each statement = station visit avoided
        "informed_consent_rate": round(confirmed / total, 3) if total else 0,
        "pretrial_risk_surface_caught": with_flags,
        "protection_pipeline_activated": protection,
        "lawyer_crossref_hours_saved_proxy": multi,  # each cluster replaces manual crossref
    }

    edge_case_coverage = {
        "intimidation": urgent > 0 or any(s.intimidation_flag for s in statements),
        "privacy_mode": privacy > 0,
        "inconsistency_engine": with_flags > 0,
        "delay_doctrine": delayed > 0 or any(s.statement_delay_days for s in statements),
        "incomplete_call_recovery": incomplete > 0,
        "multi_witness_corroboration": multi > 0,
        "language_access_ur_pa": lang_access > 0,
        "protection_referral": protection > 0,
    }

    return {
        "total_statements": total,
        "pending_review": pending,
        "urgent": urgent,
        "urgent_count": urgent,  # frontend alias
        "clusters": len(clusters),
        "cluster_count": len(clusters),  # frontend alias
        "avg_corroboration": avg_corr,
        "witness_confirmed": confirmed,
        "inconsistency_flagged": with_flags,
        "privacy_mode_uses": privacy,
        "protection_referrals": protection,
        "incomplete_calls": incomplete,
        "delayed_high_risk": delayed,
        "punjabi_or_urdu_calls": lang_access,
        "multi_witness_clusters": multi,
        "definitions": KPI_DEFINITIONS,
        "roi_proxies": roi,
        "edge_case_coverage": edge_case_coverage,
        "disclaimer": (
            "Corroboration KPIs are pre-litigation intelligence only — "
            "not admissible corroboration under CrPC Section 162."
        ),
    }
