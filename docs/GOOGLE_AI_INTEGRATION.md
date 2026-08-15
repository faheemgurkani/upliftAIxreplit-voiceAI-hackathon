# Google AI Integration — Gemini, Cloud STT, Cloud TTS

**Project:** Voice AI Enabled Orchestration Engine (Gawah) · **Product:** Gawah (گواہ)

Optional Google services sit **alongside** the existing stack — they do **not** replace Uplift AI (voice/STT/TTS) or OpenRouter/Groq (LLM).

| Layer | Primary (unchanged) | Google (optional add-on) |
|-------|---------------------|---------------------------|
| Live voice agent | Uplift Realtime Assistants | — |
| LLM structuring / flags | OpenRouter / Groq | **Gemini API** |
| Speech-to-text | Uplift STT (`ur`) | **Google Cloud Speech-to-Text** |
| Readback TTS | Uplift TTS (`defense-advocate`) | **Google Cloud Text-to-Speech** |

---

## 1. Files added

| File | Purpose |
|------|---------|
| `gawah-backend/app/services/gemini_service.py` | Gemini Developer API — `chat_json`, `chat_text` |
| `gawah-backend/app/services/google_stt_service.py` | Cloud Speech-to-Text — `transcribe` |
| `gawah-backend/app/services/google_tts_service.py` | Cloud Text-to-Speech — `synthesize_speech`, `synthesize_result` |
| `gawah-backend/scripts/google_services_test.py` | Integration probe for all three services |

Config lives in `gawah-backend/app/config.py`. Env template: `gawah-backend/.env.example`.

---

## 2. Prerequisites

### Python packages

Already listed in `gawah-backend/requirements.txt`:

```txt
google-genai>=1.33.0
google-cloud-speech>=2.31.0
google-cloud-texttospeech>=2.25.0
```

Install with the rest of the backend:

```bash
python scripts/setup.py install
# or:
pip install -r gawah-backend/requirements.txt
```

### Gemini API key

1. Create a key at [Google AI Studio](https://aistudio.google.com/apikey).
2. Set `GEMINI_API_KEY` in `gawah-backend/.env`.

### Google Cloud STT / TTS

1. Enable APIs in your GCP project:
   - [Cloud Speech-to-Text API](https://console.cloud.google.com/apis/library/speech.googleapis.com)
   - [Cloud Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)
2. Create a service account with roles that allow Speech + Text-to-Speech usage.
3. Download the JSON key and set:

```env
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/service-account.json
GOOGLE_CLOUD_PROJECT_ID=your-gcp-project-id   # optional but recommended
```

The backend also accepts the standard `GOOGLE_APPLICATION_CREDENTIALS` env var if set outside `.env`.

---

## 3. Environment variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GEMINI_API_KEY` | For Gemini | — | Gemini Developer API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Model id for `generate_content` |
| `GOOGLE_APPLICATION_CREDENTIALS` | For STT/TTS | — | Path to GCP service account JSON |
| `GOOGLE_CLOUD_PROJECT_ID` | No | — | GCP project (future Vertex use) |
| `GOOGLE_STT_LANGUAGE_CODE` | No | `ur-PK` | BCP-47 language for transcription |
| `GOOGLE_TTS_LANGUAGE_CODE` | No | `ur-IN` | BCP-47 language for synthesis |
| `GOOGLE_TTS_VOICE_NAME` | No | *(empty)* | Specific voice, e.g. `ur-IN-Wavenet-A` |
| `GOOGLE_TTS_SPEAKING_RATE` | No | `1.0` | Playback speed multiplier |

Copy from template:

```bash
cp gawah-backend/.env.example gawah-backend/.env
# edit GEMINI_API_KEY and GOOGLE_APPLICATION_CREDENTIALS
```

---

## 4. Usage in code

Import the singleton getters (same pattern as `get_llm_chat_service()` / `UpliftService`):

```python
from app.services.gemini_service import get_gemini_service
from app.services.google_stt_service import get_google_stt_service
from app.services.google_tts_service import get_google_tts_service
```

### Gemini — structured JSON (§161-style extraction)

```python
gemini = get_gemini_service()
if gemini.enabled:
    data = await gemini.chat_json(
        "Extract incident_date and sequence_of_events from this Urdu account: ...",
        system="Reply with valid JSON only.",
    )
```

### Gemini — plain text

```python
text = await gemini.chat_text("Summarize this witness statement in one sentence.")
```

### Google Cloud STT

```python
stt = get_google_stt_service()
result = await stt.transcribe(audio_bytes, filename="recording.webm")
# result: {"ok": bool, "transcript": str, "provider": "google_stt", ...}
```

Supported extensions (encoding inferred from filename): `.wav`, `.flac`, `.mp3`, `.mpeg`, `.ogg`, `.webm`, `.opus`.

### Google Cloud TTS

```python
tts = get_google_tts_service()
mp3_bytes = await tts.synthesize_speech("یہ آپ کا بیان ہے۔")
# or metadata-only helper:
meta = await tts.synthesize_result("یہ آپ کا بیان ہے۔")
```

---

## 5. Integration probe

Run the standalone probe (does not affect Uplift/OpenRouter probes):

```bash
cd gawah-backend
python scripts/google_services_test.py
```

**What it tests**

| Probe | Checks |
|-------|--------|
| `gemini.chat_json` | JSON ping via Gemini |
| `gemini.chat_text` | Plain-text response |
| `google.tts` | Urdu sample → MP3 bytes |
| `google.stt` | Round-trip: transcribe TTS output |

Results are written to `gawah-backend/data/google_services_probe_results.json`.

Missing keys produce **FAIL** rows with a clear message — the script exits non-zero if any probe fails.

---

## 6. Health check

`GET /health` and `GET /api/healthz` expose configuration flags (no secrets):

```json
{
  "gemini_configured": true,
  "gemini_model": "gemini-2.5-flash",
  "google_cloud_configured": true
}
```

Primary LLM and voice paths remain OpenRouter/Groq and Uplift unless you wire Google services into pipelines explicitly.

---

## 7. Where to plug in later (not wired by default)

These services are **available but not swapped into production paths** yet. Suggested integration points:

| Use case | Current module | Google hook |
|----------|----------------|-------------|
| Post-call §161 structuring | `web_call_pipeline.py`, `llm_service.py` | `get_gemini_service().chat_json()` |
| Consistency / corroboration | `consistency_engine.py`, `corroboration_engine.py` | Same interface as `GroqService.chat_json` |
| Web recording STT fallback | `web_call_pipeline.py` → `UpliftService.transcribe()` | `get_google_stt_service().transcribe()` if Uplift fails |
| Statement readback MP3 | `uplift_service.py` → `synthesize_speech()` | `get_google_tts_service().synthesize_speech()` as fallback |

To add Gemini to the LLM provider chain without removing OpenRouter, extend `LLMChatService` in `llm_chat_service.py` or call `get_gemini_service()` from engines when `gemini_enabled` and primary LLM is unavailable.

---

## 8. SDK references

| Service | Python package | Docs |
|---------|----------------|------|
| Gemini | `google-genai` | [python-genai README](https://github.com/googleapis/python-genai) |
| Speech-to-Text | `google-cloud-speech` | [Cloud Speech Python](https://cloud.google.com/python/docs/reference/speech/latest) |
| Text-to-Speech | `google-cloud-texttospeech` | [Cloud TTS Python](https://cloud.google.com/python/docs/reference/texttospeech/latest) |

---

## 9. Limitations

- **Not a replacement for Uplift Realtime Assistants** — Gemini Live / full voice agent is out of scope for this integration slice.
- **STT/TTS require GCP billing + enabled APIs** — free tier limits apply per Google Cloud pricing.
- **Urdu quality** — validate `ur-PK` / `ur-IN` and voice names for your demo; list voices with Cloud TTS `list_voices`.
- **Vercel** — service account JSON must be provided via env/secret; file path must exist in the serverless environment or use workload identity in GCP-hosted deploys.

---

## 10. Related docs

| Doc | |
|-----|---|
| [`UPLIFTAI_DOCUMENTATION.md`](./UPLIFTAI_DOCUMENTATION.md) | Primary voice stack |
| [`WEB_CALL_AND_DIALOGUE.md`](./WEB_CALL_AND_DIALOGUE.md) | Web call STT pipeline |
| [`LOCAL_SETUP.md`](./LOCAL_SETUP.md) | Full local install |
| [`gawah-backend/README.md`](../gawah-backend/README.md) | API runbook |
