#!/usr/bin/env python3
"""
Live integration probe against Uplift AI + OpenRouter + local Gawah API.
Does not print secret values.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

# Prefer repo-root .env
from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
load_dotenv(BACKEND / ".env", override=False)

os.chdir(BACKEND)

RESULTS: list[dict] = []


def record(name: str, ok: bool, detail: str = "", **extra):
    row = {"name": name, "ok": ok, "detail": detail, **extra}
    RESULTS.append(row)
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}", flush=True)


async def test_openrouter_direct():
    from openai import AsyncOpenAI

    key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash-0731")
    if not key:
        record("openrouter.direct", False, "OPENROUTER_API_KEY missing")
        return

    client = AsyncOpenAI(
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=key,
        timeout=45.0,
    )
    try:
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Reply with JSON only."},
                    {
                        "role": "user",
                        "content": (
                            'Return JSON {"ping":"pong","model_ok":true} and nothing else.'
                        ),
                    },
                ],
                temperature=0,
                max_tokens=64,
            ),
            timeout=50.0,
        )
        content = resp.choices[0].message.content or ""
        ok = "pong" in content.lower() or "true" in content.lower()
        record(
            "openrouter.direct",
            ok,
            f"model={model}; chars={len(content)}; preview={content[:120]!r}",
        )
    except Exception as exc:  # noqa: BLE001
        record("openrouter.direct", False, f"{type(exc).__name__}: {exc}")


async def test_uplift_tts():
    import httpx

    key = os.getenv("UPLIFTAI_API_KEY", "")
    base = os.getenv(
        "UPLIFT_BASE_URL", "https://ap-southeast-1.api.upliftai.org/v1"
    ).rstrip("/")
    if not key:
        record("uplift.tts", False, "UPLIFTAI_API_KEY missing")
        return

    voices = [
        os.getenv("UPLIFT_TTS_VOICE_ID", "v_8eelc901"),
        "v_8eelc901",
        "helpdesk-agent",
        "ai_lwr_f_fb",
    ]
    # unique preserve order
    seen = set()
    voice_list = []
    for v in voices:
        if v and v not in seen:
            seen.add(v)
            voice_list.append(v)

    async with httpx.AsyncClient(timeout=60.0) as client:
        for voice in voice_list:
            for path in (
                "/synthesis/text-to-speech/stream",
                "/synthesis/text-to-speech",
            ):
                url = f"{base}{path}"
                try:
                    resp = await client.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "voiceId": voice,
                            "text": "السلام علیکم۔ یہ گاواہ کا ٹیسٹ ہے۔",
                            "outputFormat": "MP3_22050_128",
                        },
                    )
                    ctype = resp.headers.get("content-type", "")
                    if resp.status_code < 400 and (
                        "audio" in ctype or len(resp.content) > 500
                    ):
                        out = BACKEND / "data" / "audio" / "live_tts_test.mp3"
                        out.parent.mkdir(parents=True, exist_ok=True)
                        out.write_bytes(resp.content)
                        record(
                            "uplift.tts",
                            True,
                            f"voice={voice}; endpoint={path}; bytes={len(resp.content)}",
                        )
                        return
                    detail = resp.text[:200]
                    last = f"voice={voice}; {path}; status={resp.status_code}; {detail}"
                except Exception as exc:  # noqa: BLE001
                    last = f"voice={voice}; {path}; {type(exc).__name__}: {exc}"
        record("uplift.tts", False, last)


async def test_uplift_assistant_and_session():
    import httpx

    key = os.getenv("UPLIFTAI_API_KEY", "")
    base = os.getenv(
        "UPLIFT_BASE_URL", "https://ap-southeast-1.api.upliftai.org/v1"
    ).rstrip("/")
    if not key:
        record("uplift.assistant", False, "missing key")
        return None

    # Prefer documented hackathon stack for create
    payload = {
        "name": f"Gawah Probe {int(time.time())}",
        "description": "Integration probe assistant",
        "config": {
            "agent": {
                "instructions": (
                    "You are Gawah probe. Reply briefly in Urdu. "
                    "Collect a short witness statement."
                ),
                "initialGreeting": True,
                "greetingInstructions": "السلام علیکم۔ میں گاواہ ہوں۔",
            },
            "stt": {
                "default": {
                    "provider": "soniox",
                    "model": "stt-rt-v4",
                    "language": "ur",
                }
            },
            "tts": {
                "default": {
                    "provider": "upliftai",
                    "voiceId": "helpdesk-agent",
                    "outputFormat": "MP3_22050_32",
                }
            },
            "llm": {
                "default": {"provider": "google", "model": "gemini-2.5-flash"}
            },
            "session": {"ttl": 600},
        },
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        create = await client.post(
            f"{base}/realtime-assistants",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if create.status_code >= 400:
            record(
                "uplift.assistant.create",
                False,
                f"status={create.status_code}; body={create.text[:300]}",
            )
            return None
        data = create.json()
        assistant_id = (
            data.get("realtimeAssistantId")
            or data.get("assistantId")
            or data.get("id")
        )
        record(
            "uplift.assistant.create",
            bool(assistant_id),
            f"assistant_id={assistant_id}",
        )
        if not assistant_id:
            return None

        session = await client.post(
            f"{base}/realtime-assistants/{assistant_id}/createSession",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={"participantName": "WitnessProbe"},
        )
        if session.status_code >= 400:
            record(
                "uplift.session.create",
                False,
                f"status={session.status_code}; body={session.text[:300]}",
            )
            return assistant_id
        sdata = session.json()
        token = sdata.get("token") or sdata.get("accessToken")
        ws = sdata.get("wsUrl") or sdata.get("serverUrl") or sdata.get("url")
        record(
            "uplift.session.create",
            bool(token and ws),
            f"has_token={bool(token)}; has_wsUrl={bool(ws)}; keys={list(sdata.keys())[:12]}",
        )
        return assistant_id


async def test_local_api(assistant_id: str | None):
    from fastapi.testclient import TestClient

    # Reset settings cache so env is picked up
    from app.config import get_settings
    from app.db.database import reset_db_for_tests
    from app.services.llm_chat_service import get_llm_chat_service

    get_settings.cache_clear()
    reset_db_for_tests()
    # reset llm singleton
    import app.services.llm_chat_service as lcs

    lcs._llm = None

    from app.main import app

    client = TestClient(app)

    health = client.get("/health")
    hj = health.json()
    record(
        "api.health",
        health.status_code == 200 and hj.get("llm_enabled") and hj.get("uplift_configured"),
        json.dumps(
            {
                k: hj.get(k)
                for k in (
                    "status",
                    "uplift_configured",
                    "openrouter_configured",
                    "llm_enabled",
                    "db_backend",
                )
            }
        ),
    )

    sess = client.post("/api/sessions/create", json={"participantName": "LiveTester"})
    sj = sess.json()
    record(
        "api.sessions.create",
        sess.status_code == 200 and bool(sj.get("token")),
        f"demo={sj.get('demo')}; has_ws={bool(sj.get('wsUrl') or sj.get('ws_url'))}",
    )

    # Tool chain
    client.post(
        "/api/tools/enable_privacy_mode",
        json={"session_id": "live_sess_1", "arguments": {"reason": "demo"}},
    )
    intim = client.post(
        "/api/tools/flag_intimidation",
        json={
            "session_id": "live_sess_1",
            "arguments": {"witness_statement": "mujhe daraya gaya hai"},
        },
    )
    record(
        "api.tools.flag_intimidation",
        intim.status_code == 200 and intim.json()["result"].get("escalated") is True,
        str(intim.json().get("result")),
    )

    client.post(
        "/api/tools/flag_inconsistency",
        json={
            "session_id": "live_sess_1",
            "arguments": {
                "contradiction_description": "dark vs clear face",
                "segment_a": "raat ka andhera tha",
                "segment_b": "chehra saaf dikhai diya",
                "contradiction_type": "temporal",
            },
        },
    )

    save = client.post(
        "/api/tools/save_witness_statement",
        json={
            "session_id": "live_sess_1",
            "arguments": {
                "time_of_incident": "after Isha ~9pm",
                "location": "Mohalla Hussain Abad Rawalpindi",
                "persons_present": ["Rasheed", "unknown man"],
                "sequence_of_events": (
                    "Raat ka ghup andhera tha, kuch nahi dikha. "
                    "Phir main ne uska chehra bilkul saaf dekha. "
                    "Woh akela tha. Phir dono mard andar aaye."
                ),
                "relationship_to_accused": "neighbour",
                "temporal_uncertainty": True,
                "language_of_call": "ur",
                "witness_type": "eyewitness",
                "statement_delay_days": 40,
                "statement_delay_explanation": "darr",
            },
        },
    )
    ok_save = save.status_code == 200 and "refCode" in save.json().get("result", {})
    ref1 = save.json().get("result", {}).get("refCode") if ok_save else None
    record(
        "api.tools.save_witness_statement",
        ok_save,
        f"ref={ref1}; has_readback={bool(save.json().get('result', {}).get('readbackText'))}",
    )

    # LLM chat service
    llm = get_llm_chat_service()
    record(
        "api.llm.provider",
        llm.enabled and llm.provider == "openrouter",
        f"provider={llm.provider}; model={llm.model}",
    )

    # Run engines with live LLM
    if ref1:
        from app.services.consistency_engine import run_consistency_check
        from app.services.corroboration_engine import run_corroboration_analysis

        try:
            flags = await asyncio.wait_for(run_consistency_check(ref1), timeout=120.0)
            record("engine.consistency", True, f"new_flags={len(flags)}")
        except Exception as exc:  # noqa: BLE001
            record("engine.consistency", False, f"{type(exc).__name__}: {exc}")
            flags = []

        # second statement for corroboration
        save2 = client.post(
            "/api/tools/save_witness_statement",
            json={
                "session_id": "live_sess_2",
                "arguments": {
                    "time_of_incident": "about 9pm",
                    "location": "Mohalla Hussain Abad, Rawalpindi",
                    "persons_present": ["Rasheed"],
                    "sequence_of_events": (
                        "I saw Rasheed push another man near the shop at night."
                    ),
                    "relationship_to_accused": "stranger",
                    "language_of_call": "pa",
                    "witness_type": "eyewitness",
                },
            },
        )
        ref2 = save2.json().get("result", {}).get("refCode")
        record("api.tools.save_second_witness", bool(ref2), f"ref={ref2}")

        if ref2:
            try:
                cluster = await asyncio.wait_for(
                    run_corroboration_analysis(ref2), timeout=180.0
                )
                record(
                    "engine.corroboration",
                    cluster is not None,
                    f"cluster_id={getattr(cluster, 'id', None)}; "
                    f"count={getattr(cluster, 'statement_count', None)}; "
                    f"score={getattr(cluster, 'composite_score', None)}",
                )
            except Exception as exc:  # noqa: BLE001
                record("engine.corroboration", False, f"{type(exc).__name__}: {exc}")

        detail = client.get(f"/api/statements/{ref1}")
        dj = detail.json()
        record(
            "api.statements.detail",
            detail.status_code == 200 and dj.get("ref_code") == ref1,
            f"status={dj.get('status')}; flags={len(dj.get('inconsistency_flags') or [])}; "
            f"protection={dj.get('protection', {}).get('status')}",
        )

        # Protection assessment
        prot = client.post(
            "/api/tools/assess_protection_need",
            json={
                "session_id": "live_sess_1",
                "arguments": {
                    "offence_type": "serious_assault",
                    "intimidation_already_flagged": True,
                    "province": "Punjab",
                },
            },
        )
        record(
            "api.tools.assess_protection_need",
            prot.status_code == 200 and prot.json()["result"].get("qualifies") is True,
            str(prot.json().get("result")),
        )

        conf = client.post(
            "/api/tools/confirm_statement",
            json={"session_id": "live_sess_1", "arguments": {"confirmed": True}},
        )
        record(
            "api.tools.confirm_statement",
            conf.status_code == 200 and conf.json()["result"].get("confirmed") is True,
            str(conf.json().get("result")),
        )

        listing = client.get("/api/dashboard/statements")
        record(
            "api.dashboard.statements",
            listing.status_code == 200 and listing.json().get("total", 0) >= 1,
            f"total={listing.json().get('total')}",
        )

        clusters = client.get("/api/dashboard/clusters")
        items = clusters.json().get("items") or []
        record(
            "api.dashboard.clusters",
            clusters.status_code == 200 and len(items) >= 1,
            f"count={len(items)}",
        )
        if items:
            cd = client.get(f"/api/dashboard/clusters/{items[0]['id']}")
            record(
                "api.dashboard.cluster_detail",
                cd.status_code == 200,
                f"statement_count={cd.json().get('statement_count')}",
            )

        kpis = client.get("/api/kpis")
        kj = kpis.json()
        record(
            "api.kpis",
            kpis.status_code == 200 and kj.get("total_statements", 0) >= 1,
            json.dumps(
                {
                    "total": kj.get("total_statements"),
                    "urgent": kj.get("urgent"),
                    "edge": kj.get("edge_case_coverage"),
                }
            )[:300],
        )

        # TTS via uplift service through save path may have stored audio
        audio = client.get(f"/api/statements/{ref1}/audio")
        record(
            "api.statements.audio",
            audio.status_code in {200, 404},
            f"status={audio.status_code}; "
            + (
                f"bytes={len(audio.content)}"
                if audio.status_code == 200
                else "no audio yet (TTS may have failed earlier)"
            ),
        )

        review = client.post(
            f"/api/statements/{ref1}/review",
            json={"reviewed_by": "Probe", "reviewer_notes": "live ok"},
        )
        record(
            "api.statements.review",
            review.status_code == 200 and review.json().get("status") == "reviewed",
            f"status={review.json().get('status')}",
        )

    if assistant_id:
        # Ensure env assistant id is usable by service ensure path
        os.environ["UPLIFT_ASSISTANT_ID"] = assistant_id
        get_settings.cache_clear()


async def main():
    print("=== Gawah live integration probe ===", flush=True)
    print(f"cwd={os.getcwd()}", flush=True)
    print(
        "keys_present:",
        {
            "UPLIFTAI": bool(os.getenv("UPLIFTAI_API_KEY")),
            "OPENROUTER": bool(os.getenv("OPENROUTER_API_KEY")),
            "SUPABASE": bool(os.getenv("SUPABASE_URL")),
        },
        flush=True,
    )

    await test_openrouter_direct()
    await test_uplift_tts()
    assistant_id = await test_uplift_assistant_and_session()
    await test_local_api(assistant_id)

    passed = sum(1 for r in RESULTS if r["ok"])
    failed = sum(1 for r in RESULTS if not r["ok"])
    print("\n=== SUMMARY ===")
    print(f"passed={passed} failed={failed} total={len(RESULTS)}")
    out = BACKEND / "data" / "live_probe_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(RESULTS, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
