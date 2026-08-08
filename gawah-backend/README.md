# Gawah Backend

FastAPI implementation of the full Gawah specification:

- Uplift AI Realtime Assistants + TTS/STT (Singapore region)
- Five CrPC §161 tool handlers
- Section 16 consistency engine (realtime + post-call)
- Section 17 multi-witness corroboration + collusion warning
- Witness protection referral generation
- KPI / ROI proxies + edge-case coverage metrics
- NGO lawyer dashboard APIs

## Run

```bash
# from repo root
source .venv/bin/activate
.venv/bin/pip install -r gawah-backend/requirements.txt
cp gawah-backend/.env.example gawah-backend/.env

.venv/bin/uvicorn app.main:app --app-dir gawah-backend --reload --port 8000
```

Docs: http://localhost:8000/docs

## Smoke test

```bash
.venv/bin/python gawah-backend/scripts/smoke_test.py
```

## Key routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/sessions/create` | Uplift createSession (demo fallback if no key) |
| POST | `/api/sessions/twilio-webhook` | PSTN TwiML stub |
| POST | `/api/tools/save_witness_statement` | Save + TTS readback + queue engines |
| POST | `/api/tools/flag_inconsistency` | Realtime §16 flag |
| POST | `/api/tools/flag_intimidation` | Urgent escalation + NGO webhook |
| POST | `/api/tools/enable_privacy_mode` | Anonymous mode |
| POST | `/api/tools/assess_protection_need` | Protection referral |
| POST | `/api/tools/confirm_statement` | Voice confirmation (no thumbprint) |
| GET | `/api/statements/{refCode}` | Statement detail |
| POST | `/api/statements/{refCode}/review` | Officer/NGO review |
| GET | `/api/statements/{refCode}/audio` | Readback MP3 |
| GET | `/api/dashboard/statements` | Filterable list |
| GET | `/api/dashboard/clusters` | Incident clusters |
| GET | `/api/dashboard/clusters/{id}` | Corroboration map |
| POST | `/api/internal/trigger-corroboration-analysis` | Queue §16/§17 |
| GET | `/api/kpis` | KPIs + edge-case coverage + ROI proxies |

## Uplift AI usage

1. Set `UPLIFTAI_API_KEY` (Singapore base URL default).
2. Optionally set `UPLIFT_ASSISTANT_ID`, or let `ensure_assistant()` create one with full agent instructions + tools from `app/prompts/`.
3. Frontend/demo calls `/api/sessions/create` → receives `token` + `wsUrl` for `@upliftai/assistants-react`.
4. Tool invocations from the agent hit `/api/tools/*`.
5. Readback audio via `POST /v1/synthesis/text-to-speech` (voice `ai_lwr_f_fb`).

Phone calling: only on `https://ap-southeast-1.api.upliftai.org/v1` — see `UpliftService.place_call`.

## KPIs / edge cases

`GET /api/kpis` returns operational KPIs plus:

- `roi_proxies` — literacy barrier removed, informed consent rate, protection pipeline, lawyer crossref savings
- `edge_case_coverage` — intimidation, privacy, inconsistency, delay doctrine, incomplete recovery, multi-witness, language access, protection

Corroboration disclaimer (always): *Pre-litigation intelligence only — not admissible corroboration under CrPC Section 162.*

## Compliance (future work)

Not active in MVP. See [`../docs/COMPLIANCE_FUTURE_WORK.md`](../docs/COMPLIANCE_FUTURE_WORK.md) and stub `app/services/compliance_service.py`.

Primary future targets: **CrPC §§161–162**, **PDPB 2023 / PDPA draft readiness**, **PTA/PECA call consent**, **National AI Policy 2025**.
