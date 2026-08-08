# Gawah — Uplift AI × Replit Voice AI Hackathon

Multilingual voice witness statements for Pakistan policing demos (Urdu / Punjabi / Pashto).

## Overview

**Gawah** captures a witness account over a phone call (Vapi + Uplift Orator), structures it into a legal statement with an LLM, reads it back for confirmation, and produces a printable PDF for the officer dashboard.

## Demo

- Live demo: _TBD_
- Demo video: _TBD_

## Features

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3

## Tech Stack

_TBD — fill in once the idea and stack are locked._

## Project Structure

```text
.
├── gawah-backend/   # FastAPI backend (Vapi, LLM, PDF, DB)
├── client/          # Next.js dashboard (coming next)
├── server/          # Pointer to gawah-backend
├── shared/          # Shared types, constants, utils
├── public/          # Static assets
├── assets/          # Pitch / demo / brand
├── docs/            # Brief, architecture, submission
├── scripts/         # Helper scripts
└── tests/           # Tests
```

## Getting Started

### Backend

```bash
source .venv/bin/activate
.venv/bin/pip install -r gawah-backend/requirements.txt
cp gawah-backend/.env.example gawah-backend/.env

.venv/bin/uvicorn app.main:app --app-dir gawah-backend --reload --port 8000
# Docs: http://localhost:8000/docs
.venv/bin/python gawah-backend/scripts/smoke_test.py
```

### Frontend (NGO dashboard)

```bash
cd client
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev                  # http://localhost:3000
```

Routes: `/` landing · `/demo` voice session · `/dashboard` · `/clusters`

## Environment Variables

See [`.env.example`](./.env.example) for required keys. Never commit real secrets.

## Team

| Name | Role | GitHub |
|------|------|--------|
| TBD  | TBD  | TBD    |

## License

See [LICENSE](./LICENSE).

## Hackathon

Built for the **Uplift AI × Replit Voice AI Hackathon**.
