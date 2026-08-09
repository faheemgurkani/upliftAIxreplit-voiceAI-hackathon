#!/usr/bin/env python3
"""Full-spec smoke test: tools, edge cases, consistency, corroboration, KPIs."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Isolate local store for test run
import os

os.environ["LOCAL_DB_PATH"] = str(ROOT / "data" / "smoke_store.json")

from fastapi.testclient import TestClient

from app.db.database import reset_db_for_tests
from app.main import app
from app.services import uplift_service as uplift_mod


async def _stub_readback(self, ref_code: str, text: str):  # noqa: ARG001
    path = Path(self.settings.local_audio_dir) / ref_code
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / "readback.mp3"
    file_path.write_bytes(b"ID3stub")
    return str(file_path)


def main() -> None:
    # Avoid hanging the smoke suite on live TTS
    uplift_mod.UpliftService.store_readback_audio = _stub_readback  # type: ignore[method-assign]

    reset_db_for_tests()
    store = Path(os.environ["LOCAL_DB_PATH"])
    if store.exists():
        store.unlink()

    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200, health.text
    print("health:", health.json())

    session = client.post("/api/sessions/create", json={"participantName": "Witness"})
    assert session.status_code == 200, session.text
    assert session.json().get("token")
    print("session ok")

    # Privacy mode
    priv = client.post(
        "/api/tools/enable_privacy_mode",
        json={"session_id": "sess_smoke_1", "arguments": {"reason": "sensitive"}},
    )
    assert priv.status_code == 200
    assert priv.json()["result"]["privacy_mode"] is True

    # Intimidation edge case
    intim = client.post(
        "/api/tools/flag_intimidation",
        json={
            "session_id": "sess_smoke_1",
            "arguments": {"witness_statement": "mujhe daraya gaya hai"},
        },
    )
    assert intim.status_code == 200
    assert intim.json()["result"]["escalated"] is True

    # Realtime inconsistency
    inc = client.post(
        "/api/tools/flag_inconsistency",
        json={
            "session_id": "sess_smoke_1",
            "arguments": {
                "contradiction_description": "dark vs clear face",
                "segment_a": "raat ka ghup andhera tha",
                "segment_b": "main ne uska chehra bilkul saaf dekha",
                "contradiction_type": "temporal",
            },
        },
    )
    assert inc.status_code == 200

    # Save statement 1
    save1 = client.post(
        "/api/tools/save_witness_statement",
        json={
            "session_id": "sess_smoke_1",
            "arguments": {
                "time_of_incident": "after Isha, approx 9pm",
                "location": "Mohalla Hussain Abad Rawalpindi",
                "persons_present": ["Rasheed", "ek aur aadmi"],
                "sequence_of_events": (
                    "Raat ka ghup andhera tha, kuch nahi dikha. "
                    "Phir main ne uska chehra bilkul saaf dekha. "
                    "Woh akela tha. Phir dono mard andar aaye."
                ),
                "relationship_to_accused": "neighbour",
                "temporal_uncertainty": True,
                "language_of_call": "ur",
                "witness_type": "eyewitness",
                "statement_delay_days": 35,
                "statement_delay_explanation": "darr ki wajah se",
            },
        },
    )
    assert save1.status_code == 200, save1.text
    ref1 = save1.json()["result"]["refCode"]
    print("ref1:", ref1)

    # Confirm
    conf = client.post(
        "/api/tools/confirm_statement",
        json={"session_id": "sess_smoke_1", "arguments": {"confirmed": True}},
    )
    assert conf.json()["result"]["confirmed"] is True

    # Protection
    prot = client.post(
        "/api/tools/assess_protection_need",
        json={
            "session_id": "sess_smoke_1",
            "arguments": {
                "offence_type": "serious_assault",
                "witness_is_victim": False,
                "witness_appears_under_16": False,
                "intimidation_already_flagged": True,
                "province": "Punjab",
            },
        },
    )
    assert prot.status_code == 200
    assert prot.json()["result"]["qualifies"] is True

    # Second witness — same incident (corroboration)
    save2 = client.post(
        "/api/tools/save_witness_statement",
        json={
            "session_id": "sess_smoke_2",
            "arguments": {
                "time_of_incident": "around 9 at night",
                "location": "Mohalla Hussain Abad, Rawalpindi",
                "persons_present": ["Rasheed"],
                "sequence_of_events": (
                    "I was outside when Rasheed pushed another man near the shop."
                ),
                "relationship_to_accused": "stranger",
                "language_of_call": "pa",
                "witness_type": "eyewitness",
            },
        },
    )
    assert save2.status_code == 200, save2.text
    ref2 = save2.json()["result"]["refCode"]
    print("ref2:", ref2)

    # Trigger engines synchronously for test certainty
    from app.services.consistency_engine import run_consistency_check
    from app.services.corroboration_engine import run_corroboration_analysis
    import asyncio

    asyncio.run(run_consistency_check(ref1))
    asyncio.run(run_corroboration_analysis(ref1))
    asyncio.run(run_corroboration_analysis(ref2))

    detail = client.get(f"/api/statements/{ref1}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["ref_code"] == ref1
    assert body.get("inconsistency_flags")
    assert body.get("protection", {}).get("status") == "referral_generated"
    print("flags:", len(body["inconsistency_flags"]))

    listing = client.get("/api/dashboard/statements")
    assert listing.status_code == 200
    assert listing.json()["total"] >= 2

    clusters = client.get("/api/dashboard/clusters")
    assert clusters.status_code == 200
    items = clusters.json()["items"]
    assert items, "expected at least one cluster"
    cluster_id = items[0]["id"]
    cdetail = client.get(f"/api/dashboard/clusters/{cluster_id}")
    assert cdetail.status_code == 200
    print("cluster statements:", cdetail.json().get("statement_count"))

    kpis = client.get("/api/kpis")
    assert kpis.status_code == 200
    kpi = kpis.json()
    assert kpi["total_statements"] >= 2
    assert kpi["edge_case_coverage"]["intimidation"] is True
    assert kpi["edge_case_coverage"]["privacy_mode"] is True
    print("kpis:", {k: kpi[k] for k in ("total_statements", "urgent", "clusters", "avg_corroboration")})

    review = client.post(
        f"/api/statements/{ref1}/review",
        json={"reviewed_by": "NGO Lawyer", "reviewer_notes": "Ready for counsel prep"},
    )
    assert review.status_code == 200
    assert review.json()["status"] == "reviewed"

    print("full-spec smoke test passed")


if __name__ == "__main__":
    main()
