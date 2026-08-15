#!/usr/bin/env python3
"""
Probe Google Gemini API + Cloud Speech-to-Text + Cloud Text-to-Speech.

Does not replace Uplift/OpenRouter probes — run alongside live_integration_test.py.
Does not print secret values.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

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


async def test_gemini_json():
    from app.services.gemini_service import get_gemini_service

    gemini = get_gemini_service()
    if not gemini.enabled:
        record("gemini.chat_json", False, "GEMINI_API_KEY missing")
        return

    try:
        payload = await asyncio.wait_for(
            gemini.chat_json(
                'Return JSON {"ping":"pong","provider":"gemini"} and nothing else.',
                system="Reply with valid JSON only.",
            ),
            timeout=45.0,
        )
        ok = payload.get("ping") == "pong" or payload.get("provider") == "gemini"
        record(
            "gemini.chat_json",
            ok,
            f"model={gemini.model}; keys={list(payload.keys())[:6]}",
        )
    except Exception as exc:  # noqa: BLE001
        record("gemini.chat_json", False, f"{type(exc).__name__}: {exc}")


async def test_gemini_text():
    from app.services.gemini_service import get_gemini_service

    gemini = get_gemini_service()
    if not gemini.enabled:
        record("gemini.chat_text", False, "GEMINI_API_KEY missing")
        return

    try:
        text = await asyncio.wait_for(
            gemini.chat_text("Reply with exactly: Gawah witness intake ready."),
            timeout=45.0,
        )
        ok = "gawah" in text.lower()
        record("gemini.chat_text", ok, f"chars={len(text)}; preview={text[:80]!r}")
    except Exception as exc:  # noqa: BLE001
        record("gemini.chat_text", False, f"{type(exc).__name__}: {exc}")


async def test_google_tts():
    from app.services.google_tts_service import get_google_tts_service

    tts = get_google_tts_service()
    if not tts.enabled:
        record(
            "google.tts",
            False,
            "GOOGLE_APPLICATION_CREDENTIALS missing or google-cloud-texttospeech not installed",
        )
        return None

    sample = "یہ ایک آزمائشی گواہی ہے۔"
    try:
        audio = await asyncio.wait_for(tts.synthesize_speech(sample), timeout=60.0)
        ok = len(audio) > 1000
        record("google.tts", ok, f"bytes={len(audio)}; lang={tts.settings.google_tts_language_code}")
        return audio if ok else None
    except Exception as exc:  # noqa: BLE001
        record("google.tts", False, f"{type(exc).__name__}: {exc}")
        return None


async def test_google_stt(audio_bytes: bytes | None):
    from app.services.google_stt_service import get_google_stt_service

    stt = get_google_stt_service()
    if not stt.enabled:
        record(
            "google.stt",
            False,
            "GOOGLE_APPLICATION_CREDENTIALS missing or google-cloud-speech not installed",
        )
        return

    if not audio_bytes:
        record("google.stt", False, "Skipped — no TTS audio to transcribe")
        return

    try:
        result = await asyncio.wait_for(
            stt.transcribe(audio_bytes, filename="probe.mp3"),
            timeout=90.0,
        )
        transcript = result.get("transcript") or ""
        ok = result.get("ok") and len(transcript) > 0
        record(
            "google.stt",
            ok,
            f"chars={len(transcript)}; preview={transcript[:80]!r}",
        )
    except Exception as exc:  # noqa: BLE001
        record("google.stt", False, f"{type(exc).__name__}: {exc}")


async def main() -> int:
    print("Google services probe (Gemini + Cloud STT/TTS)\n", flush=True)
    await test_gemini_json()
    await test_gemini_text()
    audio = await test_google_tts()
    await test_google_stt(audio)

    passed = sum(1 for r in RESULTS if r["ok"])
    total = len(RESULTS)
    print(f"\n{passed}/{total} passed", flush=True)

    out = BACKEND / "data" / "google_services_probe_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"results": RESULTS, "passed": passed, "total": total}, indent=2))
    print(f"Wrote {out}", flush=True)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
