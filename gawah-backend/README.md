# Gawah Backend

FastAPI backend for **Gawah** — multilingual voice witness statements (Urdu / Punjabi / Pashto) with Vapi webhooks, LLM structuring, and printable PDFs.

## Stack

| Layer | Choice |
|-------|--------|
| API | FastAPI |
| LLM | OpenAI (`gpt-4o`) |
| Voice orchestration | Vapi server webhooks |
| STT/TTS hooks | Uplift AI Orator |
| DB | Supabase (or local JSON for offline demo) |
| PDF | ReportLab |
| Deploy | Railway (recommended) / Vercel Python |

## Quick start

```bash
# from repo root — use project venv
source ../.venv/bin/activate   # or: source .venv/bin/activate from repo root
cd gawah-backend

../.venv/bin/pip install -r requirements.txt
cp .env.example .env

../.venv/bin/uvicorn app.main:app --reload --port 8000
```

Open docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Endpoints

### Vapi (`/vapi`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/vapi/call-started` | Init session + case |
| POST | `/vapi/transcript` | Structure transcript + readback |
| POST | `/vapi/call-ended` | Finalize statement |
| POST | `/vapi/confirmation` | Witness voice confirmation |
| POST | `/vapi/webhook` | Native Vapi `{ "message": ... }` envelope |

Point Vapi `assistant.server.url` to `https://<host>/vapi/webhook`.

### Statements (`/statements`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/statements/list` | Paginated list |
| GET | `/statements/{case_id}` | Latest statement for case |
| GET | `/statements/by-id/{statement_id}` | Fetch by id |
| POST | `/statements/generate-pdf` | Printable PDF |
| PUT | `/statements/{statement_id}/confirm` | Officer confirm |

### Cases (`/cases`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/cases/create` | Create case reference |
| GET | `/cases/{case_id}` | Fetch case |
| GET | `/cases/{case_id}/status` | Spoken status for Vapi readback |

## Database

1. **Local JSON (default)** — no keys needed. Store at `data/gawah_store.json`.
2. **Supabase** — set `SUPABASE_URL` + `SUPABASE_KEY`, then run `sql/schema.sql` in the Supabase SQL editor.

## Environment

See `.env.example`. Without `OPENAI_API_KEY`, the LLM service uses a deterministic heuristic so webhooks still work for demos.

## Deploy

### Railway (recommended for voice webhooks)

```bash
# set root directory to gawah-backend
# start command is in Procfile / railway.toml
```

### Vercel

Set project Root Directory to `gawah-backend`. `vercel.json` configures `app/main.py` with `maxDuration: 60`.

> For sub-500ms webhook latency under load, prefer Railway over Vercel Python cold starts.
