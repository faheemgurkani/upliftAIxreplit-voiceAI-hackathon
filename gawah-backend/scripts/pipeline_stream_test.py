#!/usr/bin/env python3
"""
Verify data streaming from call → dashboard for real operation paths.

Covers (isolated store — does not touch demo seed data):
  1. Tool path: save_witness_statement → statement on dashboard + call.ref_code
  2. Phone path: completed telephony call + transcript → process-statement → dashboard
  3. Web path: session create + recording upload → dashboard
  4. KPIs / clusters reflect streamed statements
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["LOCAL_DB_PATH"] = str(ROOT / "data" / "pipeline_stream_store.json")

from fastapi.testclient import TestClient

from app.db.database import reset_db_for_tests
from app.main import app
from app.services import uplift_service as uplift_mod


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


async def _stub_readback(self, ref_code: str, text: str):  # noqa: ARG001
    path = Path(self.settings.local_audio_dir) / ref_code
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / "readback.mp3"
    file_path.write_bytes(b"ID3stub")
    return str(file_path)


async def _stub_transcribe(self, file_bytes: bytes, filename: str = "recording.mp3"):  # noqa: ARG001
    return {"ok": False, "transcript": "", "detail": "stubbed for pipeline test"}


def main() -> None:
    # Keep pipeline tests offline for TTS/STT — statement streaming is the unit under test
    uplift_mod.UpliftService.store_readback_audio = _stub_readback  # type: ignore[method-assign]
    uplift_mod.UpliftService.transcribe = _stub_transcribe  # type: ignore[method-assign]

    reset_db_for_tests()
    store = Path(os.environ["LOCAL_DB_PATH"])
    if store.exists():
        store.unlink()

    client = TestClient(app)

    # ── Health ──────────────────────────────────────────────────────────
    health = client.get("/health")
    _assert(health.status_code == 200, health.text)
    print("✓ health")

    # ── 1) Tool path (live agent tools → dashboard) ─────────────────────
    call_id_tool = "pipe_tool_sess_1"
    client.post(
        "/api/sessions/create",
        json={"participantName": "Tool Witness"},
    )
    # Track a call row with the same session id tools will use
    from app.db.database import get_db

    db = get_db()
    db.upsert_call(
        {
            "call_id": call_id_tool,
            "status": "answered",
            "state": "answered",
            "channel": "web_browser",
            "participant_name": "Tool Witness",
            "mocked": False,
            "label": "Live — web interview in progress",
        }
    )

    save = client.post(
        "/api/tools/save_witness_statement",
        json={
            "session_id": call_id_tool,
            "arguments": {
                "time_of_incident": "after Maghrib",
                "location": "Lahore Model Town",
                "persons_present": ["Ali"],
                "sequence_of_events": (
                    "Main ne dekha ke Ali dukaan ke paas khara tha. "
                    "Phir us ne doosre aadmi ko dhakka diya."
                ),
                "language_of_call": "ur",
                "witness_type": "eyewitness",
            },
        },
    )
    _assert(save.status_code == 200, save.text)
    _assert("error" not in save.json(), save.text)
    ref_tool = save.json()["result"]["refCode"]
    _assert(bool(ref_tool), "missing ref from tool save")

    listing = client.get("/api/dashboard/statements")
    _assert(listing.status_code == 200, listing.text)
    refs = {i["ref_code"] for i in listing.json()["items"]}
    _assert(ref_tool in refs, f"tool statement {ref_tool} missing from dashboard")

    tracked = db.get_call(call_id_tool)
    _assert(tracked is not None, "call row missing")
    _assert(
        tracked.get("ref_code") == ref_tool,
        f"call.ref_code not linked (got {tracked.get('ref_code')})",
    )
    print(f"✓ tool path → dashboard ({ref_tool})")

    # ── 2) Phone path (completed PSTN + transcript → dashboard) ─────────
    call_id_phone = "pipe_phone_sess_1"
    db.upsert_call(
        {
            "call_id": call_id_phone,
            "status": "completed",
            "state": "completed",
            "channel": "phone_outbound",
            "direction": "outbound",
            "to": "+923001112233",
            "connected": True,
            "mocked": False,
            "transcript": (
                "Assalam o alaikum. Waqia Rawalpindi ke Mohalla Hussain Abad mein hua. "
                "Raat ko 9 baje Rasheed ne ek aadmi ko dhakka diya. "
                "Main eyewitness hoon. Pehle andhera tha phir chehra saaf dikha."
            ),
            "label": "Completed",
            "artifacts_available": True,
            "artifacts_status": "ready",
        }
    )

    processed = client.post(
        f"/api/sessions/calls/{call_id_phone}/process-statement",
        params={"language": "ur"},
    )
    _assert(processed.status_code == 200, processed.text)
    body = processed.json()
    _assert(body.get("ok") is True, body)
    ref_phone = body.get("ref_code")
    _assert(bool(ref_phone), "phone pipeline missing ref_code")

    listing2 = client.get("/api/dashboard/statements")
    refs2 = {i["ref_code"] for i in listing2.json()["items"]}
    _assert(ref_phone in refs2, f"phone statement {ref_phone} missing from dashboard")

    detail = client.get(f"/api/statements/{ref_phone}")
    _assert(detail.status_code == 200, detail.text)
    _assert(detail.json().get("session_id") == call_id_phone, detail.text)
    _assert(bool(detail.json().get("raw_transcript")), "raw_transcript not stored")

    phone_call = db.get_call(call_id_phone)
    _assert(phone_call.get("ref_code") == ref_phone, "phone call not linked")
    _assert(
        phone_call.get("statement_pipeline_status") == "done",
        f"pipeline status={phone_call.get('statement_pipeline_status')}",
    )
    print(f"✓ phone path → dashboard ({ref_phone})")

    # Idempotent re-run
    again = client.post(f"/api/sessions/calls/{call_id_phone}/process-statement")
    _assert(again.status_code == 200, again.text)
    _assert(again.json().get("ref_code") == ref_phone, again.text)
    _assert(again.json().get("skipped") is True, "expected skip on second run")
    print("✓ phone path idempotent")

    # Auto-stream via GET /calls?sync=false for a second local completed call
    call_id_auto = "pipe_phone_auto_2"
    db.upsert_call(
        {
            "call_id": call_id_auto,
            "status": "completed",
            "state": "completed",
            "channel": "telephony",
            "mocked": False,
            "connected": True,
            "transcript": (
                "Main ne dekha ke do mard dukaan ke bahar lar rahe the. "
                "Waqia Karachi Gulshan mein shaam ko hua."
            ),
            "label": "Completed",
        }
    )
    calls = client.get("/api/sessions/calls", params={"limit": 20, "sync": False})
    _assert(calls.status_code == 200, calls.text)
    auto_row = next(
        (c for c in calls.json()["items"] if c.get("call_id") == call_id_auto),
        None,
    )
    _assert(auto_row is not None, "auto call missing from list")
    _assert(bool(auto_row.get("ref_code")), f"auto-stream failed: {auto_row}")
    ref_auto = auto_row["ref_code"]
    listing3 = client.get("/api/dashboard/statements")
    _assert(
        ref_auto in {i["ref_code"] for i in listing3.json()["items"]},
        f"auto-streamed {ref_auto} not on dashboard",
    )
    print(f"✓ phone auto-stream via /calls ({ref_auto})")

    # ── 3) Web recording path ───────────────────────────────────────────
    session = client.post(
        "/api/sessions/create",
        json={"participantName": "Web Witness"},
    )
    _assert(session.status_code == 200, session.text)
    web_call_id = session.json().get("sessionId") or session.json().get("session_id")
    if not web_call_id:
        # Demo fallback still tracks a call — pick newest web call
        web_calls = [
            c
            for c in db.list_calls(limit=10)
            if "web" in str(c.get("channel") or "")
        ]
        _assert(web_calls, "no web call tracked after session create")
        web_call_id = web_calls[0]["call_id"]

    # Minimal fake webm bytes (pipeline tolerates STT failure + heuristic structure)
    fake_audio = b"FAKEWEBM" + os.urandom(256)
    upload = client.post(
        f"/api/sessions/web/{web_call_id}/recording",
        files={"file": ("testimony.webm", fake_audio, "audio/webm")},
        data={"language": "ur", "participantName": "Web Witness"},
    )
    _assert(upload.status_code == 200, upload.text)
    up = upload.json()
    _assert(up.get("ok") is True, up)
    ref_web = up.get("ref_code")
    _assert(bool(ref_web), "web pipeline missing ref_code")

    listing4 = client.get("/api/dashboard/statements")
    _assert(
        ref_web in {i["ref_code"] for i in listing4.json()["items"]},
        f"web statement {ref_web} missing from dashboard",
    )
    print(f"✓ web recording path → dashboard ({ref_web})")

    # ── 4) KPIs reflect streamed ops ────────────────────────────────────
    kpis = client.get("/api/kpis")
    _assert(kpis.status_code == 200, kpis.text)
    kpi = kpis.json()
    _assert(kpi.get("total_statements", 0) >= 4, kpi)
    print(
        "✓ kpis:",
        {
            k: kpi.get(k)
            for k in ("total_statements", "urgent", "clusters", "avg_corroboration")
        },
    )

    # Activity feed carries ref_codes from streamed calls
    activity = client.get("/api/sessions/activity", params={"limit": 40})
    _assert(activity.status_code == 200, activity.text)
    feed_refs = {
        i.get("ref_code") for i in activity.json().get("items") or [] if i.get("ref_code")
    }
    _assert(ref_phone in feed_refs, "phone ref missing from activity feed")
    print("✓ activity feed includes streamed ref_codes")

    print("\npipeline stream test passed — call→dashboard streaming verified")


if __name__ == "__main__":
    main()
