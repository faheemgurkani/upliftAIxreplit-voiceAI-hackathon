from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.db.database import Database, get_db
from app.models.cluster import IncidentCluster
from app.models.statement import StatementRecord
from app.services.groq_service import GroqService, get_groq_service

FIELD_WEIGHTS = {
    "time_of_incident": 0.15,
    "location": 0.25,
    "persons_present": 0.25,
    "sequence_of_events": 0.25,
    "relationship_to_accused": 0.10,
}

URDU_STOP = {
    "mein",
    "main",
    "aur",
    "ka",
    "ki",
    "ke",
    "se",
    "par",
    "tha",
    "thi",
    "the",
    "hai",
    "hain",
    "ek",
    "ko",
}


def jaccard_location(a: str, b: str) -> float:
    tokens_a = {
        t for t in (a or "").lower().split() if len(t) > 3 and t not in URDU_STOP
    }
    tokens_b = {
        t for t in (b or "").lower().split() if len(t) > 3 and t not in URDU_STOP
    }
    if not tokens_a or not tokens_b:
        return 0.0
    inter = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    return inter / union if union else 0.0


def heuristic_field_compare(field_name: str, values: List[str]) -> Dict[str, Any]:
    normalized = [v.strip().lower() for v in values if v]
    if len(normalized) < 2:
        return {
            "field": field_name,
            "status": "insufficient_data",
            "agreement_score": None,
            "values": values,
        }
    unique = set(normalized)
    if len(unique) == 1:
        status = "collusion_warning" if field_name == "sequence_of_events" else "agreement"
        score = 0.99 if status == "collusion_warning" else 1.0
        if status == "agreement" and field_name == "sequence_of_events":
            # Near-identical long narratives → collusion proximity
            if len(normalized[0]) > 80:
                status = "collusion_warning"
                score = 0.97
        return {
            "field": field_name,
            "status": status,
            "agreement_score": score,
            "values": values,
            "conflict_detail": None,
            "explainable": True,
        }
    # Token overlap average
    scores = []
    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            scores.append(jaccard_location(normalized[i], normalized[j]))
    avg = sum(scores) / len(scores) if scores else 0.0
    if avg >= 0.7:
        status = "agreement"
    elif avg >= 0.4:
        status = "partial_agreement"
    else:
        status = "conflict"
    return {
        "field": field_name,
        "status": status,
        "agreement_score": round(avg, 3),
        "values": values,
        "conflict_detail": "Accounts differ" if status == "conflict" else None,
        "explainable": status != "conflict",
        "explanation": "May reflect different vantage points" if status != "agreement" else None,
    }


async def compare_field(
    field_name: str, values: List[Any], groq: GroqService
) -> Dict[str, Any]:
    non_null = []
    for v in values:
        if v is None or v == "":
            continue
        if isinstance(v, list):
            non_null.append(", ".join(str(x) for x in v))
        else:
            non_null.append(str(v))

    if len(non_null) < 2:
        return {
            "field": field_name,
            "status": "insufficient_data" if non_null else "single",
            "agreement_score": None,
            "values": non_null,
        }

    if not groq.enabled:
        return heuristic_field_compare(field_name, non_null)

    prompt = f"""You are a legal analyst comparing witness statements about the same incident.
Compare these {len(non_null)} witness accounts of the same field: "{field_name}".

{chr(10).join(f'Witness {i+1}: "{v}"' for i, v in enumerate(non_null))}

Respond ONLY with JSON:
{{
  "status": "agreement" | "partial_agreement" | "conflict" | "collusion_warning",
  "agreement_score": 0.0-1.0,
  "conflict_detail": "brief",
  "explainable": true/false,
  "explanation": "why discrepancy may be innocent"
}}
If agreement_score > 0.95 on sequence_of_events with near-identical phrasing, use collusion_warning."""
    result = await groq.chat_json(prompt)
    if not result:
        return heuristic_field_compare(field_name, non_null)
    # Collusion safeguard
    score = result.get("agreement_score")
    if (
        field_name == "sequence_of_events"
        and score is not None
        and float(score) > 0.95
        and result.get("status") == "agreement"
    ):
        result["status"] = "collusion_warning"
    return {"field": field_name, **result, "values": non_null}


def composite_score(field_results: List[Dict[str, Any]]) -> Optional[float]:
    weighted_sum = 0.0
    total_weight = 0.0
    for fr in field_results:
        weight = FIELD_WEIGHTS.get(fr.get("field", ""), 0)
        score = fr.get("agreement_score")
        if score is not None and weight:
            weighted_sum += float(score) * weight
            total_weight += weight
    if total_weight <= 0:
        return None
    return round(weighted_sum / total_weight, 3)


def generate_consensus_summary(
    statements: List[StatementRecord], field_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    agreed = [
        f
        for f in field_results
        if f.get("status") in {"agreement", "partial_agreement"}
        or (f.get("agreement_score") is not None and float(f["agreement_score"]) > 0.7)
    ]
    conflicted = [
        f
        for f in field_results
        if f.get("status") == "conflict"
        or (
            f.get("agreement_score") is not None
            and float(f["agreement_score"]) < 0.4
            and f.get("status") not in {"insufficient_data", "single"}
        )
    ]
    collusion = [f for f in field_results if f.get("status") == "collusion_warning"]
    return {
        "statement_count": len(statements),
        "fields_agreed": [f.get("field") for f in agreed],
        "fields_conflicted": [
            {
                "field": f.get("field"),
                "detail": f.get("conflict_detail"),
                "explainable": f.get("explainable"),
            }
            for f in conflicted
        ],
        "collusion_warnings": [f.get("field") for f in collusion],
        "recommendation": (
            "Strong corroboration — witnesses agree on all key fields. Prepare for court."
            if not conflicted
            else (
                f"{len(conflicted)} field(s) in conflict — resolve before submission: "
                + ", ".join(str(f.get("field")) for f in conflicted)
                + "."
            )
        ),
        "disclaimer": (
            "Pre-litigation intelligence only — not admissible corroboration "
            "under CrPC Section 162."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def run_corroboration_analysis(
    new_ref_code: str,
    *,
    db: Database | None = None,
    groq: GroqService | None = None,
) -> Optional[IncidentCluster]:
    """Section 17 — cluster + field-level corroboration (background)."""
    db = db or get_db()
    groq = groq or get_groq_service()
    new_stmt = db.get_statement_by_ref(new_ref_code)
    if not new_stmt:
        return None

    window_start = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
    candidates = db.recent_statements(window_start, exclude_ref=new_ref_code)

    best_cluster_id: Optional[str] = None
    best_score = 0.0

    for candidate in candidates:
        spatial = jaccard_location(new_stmt.location or "", candidate.location or "")
        temporal_ok = True  # already filtered by 72h window
        signals = 0
        if spatial >= 0.5:
            signals += 1
        if temporal_ok:
            signals += 1

        semantic_conf = 0.0
        if spatial >= 0.5:
            if groq.enabled:
                r = await groq.chat_json(
                    f"""Do these two witness accounts plausibly describe the same incident?
Account 1 location: "{new_stmt.location}" | narrative: "{(new_stmt.sequence_of_events or '')[:300]}"
Account 2 location: "{candidate.location}" | narrative: "{(candidate.sequence_of_events or '')[:300]}"
Respond ONLY with JSON: {{"same_incident": true/false, "confidence": 0.0-1.0}}"""
                )
                if r.get("same_incident"):
                    semantic_conf = float(r.get("confidence") or 0)
                    signals += 1
            else:
                # heuristic semantic: shared tokens in narrative
                semantic_conf = jaccard_location(
                    new_stmt.sequence_of_events or "",
                    candidate.sequence_of_events or "",
                )
                if semantic_conf >= 0.25:
                    signals += 1

        if signals >= 2 and semantic_conf >= best_score:
            best_score = semantic_conf
            best_cluster_id = candidate.incident_cluster_id

    if not best_cluster_id:
        cluster = IncidentCluster(
            cluster_label=f"{new_stmt.location} — {datetime.now(timezone.utc).date()}",
            incident_location=new_stmt.location,
            statement_count=1,
        )
        cluster = db.save_cluster(cluster)
        best_cluster_id = cluster.id
    else:
        cluster = db.get_cluster(best_cluster_id)
        if cluster is None:
            cluster = IncidentCluster(
                id=best_cluster_id,
                cluster_label=new_stmt.location,
                incident_location=new_stmt.location,
            )
            cluster = db.save_cluster(cluster)

    new_stmt.incident_cluster_id = best_cluster_id
    db.save_statement(new_stmt)

    cluster_stmts = db.list_statements_in_cluster(best_cluster_id)
    if len(cluster_stmts) < 2:
        cluster.statement_count = len(cluster_stmts)
        return db.save_cluster(cluster)

    fields = [
        "time_of_incident",
        "location",
        "persons_present",
        "sequence_of_events",
        "relationship_to_accused",
    ]
    field_results = []
    for field in fields:
        values = [getattr(s, field) for s in cluster_stmts]
        field_results.append(await compare_field(field, values, groq))

    score = composite_score(field_results)
    consensus = generate_consensus_summary(cluster_stmts, field_results)
    collusion = any(f.get("status") == "collusion_warning" for f in field_results)

    cluster.statement_count = len(cluster_stmts)
    cluster.consensus_summary = consensus
    cluster.conflict_map = field_results
    cluster.composite_score = score
    cluster.collusion_warning = collusion
    cluster.updated_at = datetime.now(timezone.utc)
    cluster = db.save_cluster(cluster)

    for stmt in cluster_stmts:
        stmt.corroboration_score = score
        stmt.corroboration_detail = {
            "field_results": field_results,
            "disclaimer": consensus["disclaimer"],
        }
        db.save_statement(stmt)

    db.record_kpi_event(
        "corroboration_run",
        {
            "ref_code": new_ref_code,
            "cluster_id": best_cluster_id,
            "score": score,
            "collusion_warning": collusion,
        },
    )
    return cluster
