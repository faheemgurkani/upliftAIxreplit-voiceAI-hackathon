#!/usr/bin/env python3
"""Quick local smoke test for Gawah API (no external keys required)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200, health.text
    print("health:", health.json())

    case = client.post("/cases/create", json={"station_id": "LHR", "title": "Demo case"})
    assert case.status_code == 200, case.text
    case_id = case.json()["case_id"]
    print("case:", case_id)

    started = client.post(
        "/vapi/call-started",
        json={"call_id": "call_smoke_1", "language": "urdu", "case_id": case_id},
    )
    assert started.status_code == 200, started.text

    transcript = client.post(
        "/vapi/transcript",
        json={
            "call_id": "call_smoke_1",
            "case_id": case_id,
            "language": "urdu",
            "is_final": True,
            "transcript": (
                "میرا نام احمد ہے۔ کل شام پانچ بجے ماڈل ٹاؤن میں میں نے دیکھا کہ "
                "دو افراد دکان کے سامنے جھگڑا کر رہے تھے۔ پھر ایک نے دوسرے کو دھکا دیا۔"
            ),
        },
    )
    assert transcript.status_code == 200, transcript.text
    body = transcript.json()
    assert "response" in body
    print("readback:", body["response"][:120], "...")

    statement = client.get(f"/statements/{case_id}")
    assert statement.status_code == 200, statement.text
    statement_id = statement.json()["id"]

    pdf = client.post("/statements/generate-pdf", json={"statement_id": statement_id})
    assert pdf.status_code == 200, pdf.text
    assert pdf.headers["content-type"].startswith("application/pdf")
    assert len(pdf.content) > 500
    print("pdf bytes:", len(pdf.content))

    confirm = client.put(f"/statements/{statement_id}/confirm", json={"officer_name": "ASI Demo"})
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["officer_confirmed"] is True
    print("smoke test passed")


if __name__ == "__main__":
    main()
