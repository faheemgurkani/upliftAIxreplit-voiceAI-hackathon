# Gawah (گواہ) — Uplift AI × Replit Voice AI Hackathon

Voice-first witness statements for Pakistan: a neighbour speaks on a **browser WebRTC** or **PSTN** call; counsel gets a structured CrPC **§161** record, consistency flags, and multi-witness clusters — without putting the caller’s identity on the dashboard.

> **Spine:** A witness can go on record without going on record — and counsel can act on that record before the case collapses.

---

## Quick start (teammates)

**Prerequisites:** Python 3.10+, Node.js 18+, Git.  
**Full guide:** [`docs/LOCAL_SETUP.md`](./docs/LOCAL_SETUP.md)

### macOS / Linux

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh install   # venv, deps, env files, pnpm, demo seed
./scripts/setup.sh dev       # API :8000 + UI :5173
```

### Windows (PowerShell)

```powershell
.\scripts\setup.ps1 install
.\scripts\setup.ps1 dev
```

### Any OS

```bash
python scripts/setup.py install   # Windows: py -3 scripts\setup.py install
python scripts/setup.py dev
```

| Open | URL |
|------|-----|
| App | http://127.0.0.1:5173 |
| API docs | http://127.0.0.1:8000/docs |

Put live keys in **`gawah-backend/.env`** (see [Environment](#environment-variables)). Then tour: **Dashboard → NBRA7K → Clusters → Calls → Demo (live call)**.

```bash
python scripts/setup.py check   # verify tools / env
python scripts/setup.py seed    # reload demo statements
```

---

## Overview

**Gawah** captures a witness account over **web WebRTC** or **PSTN** (Uplift AI, Singapore region), structures CrPC §161 fields, flags inconsistencies, clusters overlapping incidents, and surfaces a lawyer / NGO review queue. Witnesses stay free; institutions buy seats.

The agent speaks **male Standard Urdu** (Uplift voice `defense-advocate`) and is instructed to output **Nastaliq Urdu** so live captions match what the witness hears.

## Features

- Live **web** and **phone** voice intake (Urdu / Punjabi, Shahmukhi/Nastaliq)
- **Live Agent ↔ Witness dialogue** on `/demo` (scrollable chat beside the call panel)
- End-of-call **mic upload → STT → §161 structuring** for web sessions (dashboard statement + ref code)
- Privacy mode + 6-character reference code (no phone on the dashboard)
- Consistency flags (A/B segments) for counsel prep — not lie detection
- Multi-witness **clusters** with agreement / conflict / collusion caution (§162 honesty)
- Protection referral when intimidation is indicated
- Seeded demo data for offline tour of Dashboard / Clusters / Calls

## How a live web call works

```text
Browser (/demo)
  → POST /api/sessions/create  (adhoc Uplift session: full Gawah prompt + tools + Urdu STT/TTS)
  → @upliftai/assistants-react  (WebRTC room)
  → LiveKit transcriptions → Agent / گواہ chat (right panel, fixed height, scrolls)
  → Continuous witness MediaRecorder
  → End call → POST /api/sessions/web/{callId}/recording
       (+ optional dialogue JSON)
       → STT → structure fields → statement + ref code
  → POST /api/sessions/web/{callId}/complete
  → Ended UI: CTAs + full dialogue chat
```

Phone path uses the same agent config (synced to `UPLIFT_ASSISTANT_ID`) via `POST /api/sessions/call` on the Singapore base URL.

## Tech stack

| Layer | Stack |
|-------|--------|
| API | FastAPI · Uplift AI (Realtime Assistants, TTS, STT) · OpenRouter · local JSON store |
| UI | Vite · React · Tailwind · `@upliftai/assistants-react` · LiveKit components |
| Package manager (UI) | **pnpm** workspace under `frontend/` |

## Project structure

```text
.
├── gawah-backend/                      # FastAPI — run this API
│   ├── app/prompts/                    # Agent instructions + tool schemas
│   ├── app/services/                   # Uplift, web pipeline, consistency, clusters
│   └── scripts/seed_demo.py            # Demo statements / cluster / calls
├── frontend/artifacts/gawah-frontend/  # Vite UI — run this frontend
│   └── src/components/
│       ├── live-web-call.tsx           # WebRTC + dialogue + recording
│       └── transcript-chat.tsx         # Agent / گواہ chat UI
├── frontend/                           # pnpm workspace root
├── client/                             # older Next.js prototype (optional)
├── docs/                               # Specs, setup, compliance
├── scripts/                            # setup.py / setup.sh / setup.ps1
└── tests/                              # Test notes
```

`frontend/` is a normal folder in this repo (not a git submodule).

---

## Environment variables

Templates:

- [`.env.example`](./.env.example) — root convenience copy  
- [`gawah-backend/.env.example`](./gawah-backend/.env.example) — **used by the API**  
- [`frontend/artifacts/gawah-frontend/.env.example`](./frontend/artifacts/gawah-frontend/.env.example)

**Required for live voice / phone:**

```env
UPLIFTAI_API_KEY=
UPLIFT_BASE_URL=https://ap-southeast-1.api.upliftai.org/v1
```

**Recommended:**

```env
OPENROUTER_API_KEY=
UPLIFT_ASSISTANT_ID=              # optional; backend creates/syncs
UPLIFT_TTS_VOICE_ID=defense-advocate   # male Standard Urdu (see Uplift voice library)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Never commit real secrets. Ask the team for keys privately.

Voice catalog: [docs.upliftai.org/orator_voices](https://docs.upliftai.org/orator_voices).

---

## Manual run (without the script)

```bash
# API
python3 -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r gawah-backend/requirements.txt
cp gawah-backend/.env.example gawah-backend/.env
uvicorn app.main:app --app-dir gawah-backend --reload --host 0.0.0.0 --port 8000

# UI (second terminal)
cd frontend && pnpm install
cd artifacts/gawah-frontend
cp .env.example .env
PORT=5173 BASE_PATH=/ pnpm dev --host 127.0.0.1
```

More detail: [`gawah-backend/README.md`](./gawah-backend/README.md) · [`docs/LOCAL_SETUP.md`](./docs/LOCAL_SETUP.md)

---

## Demo routes

| Path | Purpose |
|------|---------|
| `/` | Landing |
| `/demo` | Live web / phone call + dialogue + activity log |
| `/dashboard` | Statement queue |
| `/dashboard/:ref` | Statement detail |
| `/clusters` | Incident clusters |
| `/calls` | Live call pipeline |

### Seeded refs (after `seed`)

| Ref | Notes |
|-----|--------|
| **NBRA7K** | Urgent, privacy, intimidation, A/B flags, protection |
| **SHPK2M** | Phone / shopkeeper, sequence flag |
| **NBRC9Q** | Punjabi, privacy, collusion caution vs shopkeeper |

Cluster: Hussain Abad (`26980a20-demo-hussain-abad-0001`) + linked calls.

---

## Key API surfaces

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/sessions/create` | Adhoc WebRTC session (`token` + `wsUrl`) |
| POST | `/api/sessions/call` | Outbound PSTN (Pakistan mobiles) |
| POST | `/api/sessions/web/{id}/recording` | Mic upload + optional `dialogue` JSON → STT → statement |
| POST | `/api/sessions/web/{id}/complete` | Mark web session ended + ensure dashboard row |
| POST | `/api/sessions/web/{id}/events` | Activity / pipeline events |
| GET | `/api/dashboard/statements` | Review queue |
| GET | `/api/dashboard/clusters` | Multi-witness clusters |
| GET | `/api/kpis` | Ops + ROI proxies |

Full contract: [`docs/BACKEND_PRD_FOR_FRONTEND.md`](./docs/BACKEND_PRD_FOR_FRONTEND.md).

---

## Docs

| Doc | What |
|-----|------|
| [`docs/LOCAL_SETUP.md`](./docs/LOCAL_SETUP.md) | Teammate install / troubleshooting |
| [`docs/WEB_CALL_AND_DIALOGUE.md`](./docs/WEB_CALL_AND_DIALOGUE.md) | Live web call + dialogue + upload pipeline |
| [`docs/BACKEND_PRD_FOR_FRONTEND.md`](./docs/BACKEND_PRD_FOR_FRONTEND.md) | API contract for the UI |
| [`docs/UPLIFTAI_DOCUMENTATION.md`](./docs/UPLIFTAI_DOCUMENTATION.md) | Uplift hackathon guide (TTS / calls) |
| [`docs/FULL_SPEC_AND_IMPLEMENTATION_PLAN.md`](./docs/FULL_SPEC_AND_IMPLEMENTATION_PLAN.md) | Full product spec |
| [`docs/COMPLIANCE_FUTURE_WORK.md`](./docs/COMPLIANCE_FUTURE_WORK.md) | CrPC / PDPA track |
| [`docs/PAKISTAN_LIVE_VERIFICATION_REPORT.md`](./docs/PAKISTAN_LIVE_VERIFICATION_REPORT.md) | Live stack probe notes |
| [`gawah-backend/README.md`](./gawah-backend/README.md) | API runbook + routes |
| [`scripts/README.md`](./scripts/README.md) | Setup script commands |

## Compliance (future work)

Hackathon MVP is **not** claiming full statutory privacy certification. Post-demo targets: CrPC §§161–162, PDPB/PDPA draft readiness, PTA/PECA consent, National AI Policy 2025 — see compliance doc above.

## License

See [LICENSE](./LICENSE).

## Hackathon

Built for the **Uplift AI × Replit Voice AI Hackathon 2026**.
