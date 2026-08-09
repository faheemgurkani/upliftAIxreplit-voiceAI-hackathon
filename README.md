# Gawah (گواہ) — Uplift AI × Replit Voice AI Hackathon

Voice-first witness statements for Pakistan: a neighbour speaks on a phone or browser call; counsel gets a structured §161 record, consistency flags, and multi-witness clusters — without putting the caller’s identity on the dashboard.

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

Put live keys in `gawah-backend/.env` (see [Environment](#environment-variables)). Then demo: **Dashboard → NBRA7K → Clusters → Calls → Demo (live call)**.

```bash
python scripts/setup.py check   # verify tools / env
python scripts/setup.py seed    # reload demo statements
```

---

## Overview

**Gawah** captures a witness account over **web WebRTC** or **PSTN** (Uplift AI, Singapore), structures CrPC §161 fields, flags inconsistencies, clusters overlapping incidents, and surfaces a lawyer / NGO review queue. Witnesses stay free; institutions buy seats.

## Features

- Live **web** and **phone** voice intake (Urdu / Punjabi)
- Privacy mode + reference code (no phone on the dashboard)
- Consistency flags (A/B segments) for counsel prep — not lie detection
- Multi-witness **clusters** with agreement / conflict / collusion caution (§162 honesty)
- Protection referral when intimidation is indicated
- Seeded demo data for offline tour of Dashboard / Clusters / Calls

## Tech stack

| Layer | Stack |
|-------|--------|
| API | FastAPI · Uplift AI · OpenRouter · local JSON store (optional Supabase) |
| UI | Vite · React · Tailwind · `@upliftai/assistants-react` |
| Package manager (UI) | **pnpm** workspace under `frontend/` |

## Project structure

```text
.
├── gawah-backend/                      # FastAPI — run this API
├── frontend/artifacts/gawah-frontend/  # Vite UI — run this frontend
├── frontend/                           # pnpm workspace root
├── client/                             # older Next.js prototype (optional)
├── docs/                               # Specs, setup, compliance
├── scripts/                            # setup.py / setup.sh / setup.ps1
└── tests/                              # Test notes
```

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
UPLIFT_ASSISTANT_ID=          # optional; backend can create/patch
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

Never commit real secrets. Ask the team for keys privately.

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
| `/demo` | Live web / phone call |
| `/dashboard` | Statement queue |
| `/dashboard/:ref` | Statement detail |
| `/clusters` | Incident clusters |
| `/calls` | Live call pipeline |

## Docs

| Doc | What |
|-----|------|
| [`docs/LOCAL_SETUP.md`](./docs/LOCAL_SETUP.md) | Teammate install / troubleshooting |
| [`docs/BACKEND_PRD_FOR_FRONTEND.md`](./docs/BACKEND_PRD_FOR_FRONTEND.md) | API contract |
| [`docs/UPLIFTAI_DOCUMENTATION.md`](./docs/UPLIFTAI_DOCUMENTATION.md) | Uplift notes |
| [`docs/FULL_SPEC_AND_IMPLEMENTATION_PLAN.md`](./docs/FULL_SPEC_AND_IMPLEMENTATION_PLAN.md) | Full product spec |
| [`docs/COMPLIANCE_FUTURE_WORK.md`](./docs/COMPLIANCE_FUTURE_WORK.md) | CrPC / PDPA track |

## Pakistan live verification

Live stack probe report: [`docs/PAKISTAN_LIVE_VERIFICATION_REPORT.md`](./docs/PAKISTAN_LIVE_VERIFICATION_REPORT.md).

## Compliance (future work)

Hackathon MVP is **not** claiming full statutory privacy certification. Post-demo targets: CrPC §§161–162, PDPB/PDPA draft readiness, PTA/PECA consent, National AI Policy 2025 — see compliance doc above.

## License

See [LICENSE](./LICENSE).

## Hackathon

Built for the **Uplift AI × Replit Voice AI Hackathon 2026**.
