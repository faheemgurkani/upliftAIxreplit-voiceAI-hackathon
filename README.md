# Voice AI Enabled Orchestration Engine (Gawah)

**Gawah (گواہ)** — voice-first CrPC **§161** witness statements for Pakistan. Witnesses speak via **WebRTC** or **PSTN**; counsel gets structured records, consistency flags, and multi-witness clusters — without caller identity on the dashboard.

> **[Uplift AI × Replit Voice AI Hackathon (2026)](https://upliftai.org)** · Voice realtime, STT, and TTS by **[Uplift AI](https://upliftai.org)** (Singapore)

[![Live on Vercel](https://img.shields.io/badge/Live%20demo-upliftaixreplit--gawah.vercel.app-000?style=for-the-badge&logo=vercel&logoColor=white)](https://upliftaixreplit-gawah.vercel.app)

| | URL |
|---|-----|
| **App** | https://upliftaixreplit-gawah.vercel.app |
| **API** | https://gawah-backend.vercel.app · [docs](https://gawah-backend.vercel.app/docs) · [health](https://gawah-backend.vercel.app/health) |

Production deploy: [`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md)

---

## Quick start

**Prerequisites:** Python 3.10+, Node.js 18+, Git · Full guide: [`docs/LOCAL_SETUP.md`](./docs/LOCAL_SETUP.md)

```bash
python scripts/setup.py install
python scripts/setup.py dev
```

| Local | URL |
|-------|-----|
| App | http://127.0.0.1:5173 |
| API | http://127.0.0.1:8000/docs |

Copy [`gawah-backend/.env.example`](./gawah-backend/.env.example), add keys (below), then tour **Dashboard → NBRA7K → Clusters → Calls → Demo**.

---

## Features

- Web + phone voice intake (Urdu / Punjabi) through Uplift AI
- End-of-call STT → §161 structure → 6-character ref code + privacy mode
- Consistency flags, multi-witness clusters, protection referrals
- Seeded demo data (`NBRA7K`, `SHPK2M`, `NBRC9Q`) for offline UI tour

## Stack

| Layer | Tech |
|-------|------|
| API | FastAPI · Uplift AI · OpenRouter · local JSON |
| UI | Vite · React · `@upliftai/assistants-react` |

```text
gawah-backend/                       # FastAPI orchestration
frontend/artifacts/gawah-frontend/   # production UI
docs/                                # specs, deploy, API contract
```

---

## Environment

Minimum for live voice (see [`gawah-backend/.env.example`](./gawah-backend/.env.example)):

```env
UPLIFTAI_API_KEY=
UPLIFT_BASE_URL=https://ap-southeast-1.api.upliftai.org/v1
OPENROUTER_API_KEY=   # recommended — structuring
```

Do not commit secrets.

---

## Documentation

| Doc | |
|-----|---|
| [`docs/LOCAL_SETUP.md`](./docs/LOCAL_SETUP.md) | Install & troubleshooting |
| [`docs/DEPLOYMENT.md`](./docs/DEPLOYMENT.md) | Vercel production |
| [`docs/BACKEND_PRD_FOR_FRONTEND.md`](./docs/BACKEND_PRD_FOR_FRONTEND.md) | API contract |
| [`docs/WEB_CALL_AND_DIALOGUE.md`](./docs/WEB_CALL_AND_DIALOGUE.md) | Live call pipeline |
| [`docs/FULL_SPEC_AND_IMPLEMENTATION_PLAN.md`](./docs/FULL_SPEC_AND_IMPLEMENTATION_PLAN.md) | Full product spec |
| [`docs/UPLIFTAI_DOCUMENTATION.md`](./docs/UPLIFTAI_DOCUMENTATION.md) | Uplift AI integration guide |
| [`gawah-backend/README.md`](./gawah-backend/README.md) | API runbook |

---

## Team

| Contributor | GitHub |
|-------------|--------|
| Zeeshan | [@Xeeshan85](https://github.com/Xeeshan85) |

---

## License

See [LICENSE](./LICENSE).
