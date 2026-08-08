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

## Phone calling (report an incident by PSTN)

Uplift AI places **outbound** calls to Pakistani mobiles only (Singapore region). You do **not** need your own caller ID.

### Call me (easiest)

1. Backend running with `UPLIFTAI_API_KEY` and `UPLIFT_BASE_URL=https://ap-southeast-1.api.upliftai.org/v1`
2. Open frontend **Demo → Phone call**, enter `+92…` / `03…`, click **Call me**
3. Answer the phone — Gawah runs the §161 interview
4. Or via API:

```bash
curl -X POST http://localhost:8000/api/sessions/call \
  -H 'Content-Type: application/json' \
  -d '{"to":"+923001234567","participantName":"Witness"}'
```

Poll status: `GET /api/sessions/calls`

### Receive a call (witness dials in)

Uplift does not expose inbound DIDs. Pattern used here:

1. Buy/configure a **Twilio** Pakistani (or reachable) number
2. Expose your API publicly (`ngrok http 8000`)
3. Set the number’s Voice webhook to `POST https://<public>/api/sessions/twilio-webhook`
4. Set `TWILIO_*` in `.env` (optional metadata)
5. Witness dials Twilio → TwiML greets them → we **call them back** via Uplift with the Gawah agent

Full Twilio Media Streams ↔ WebRTC bridge is still deferred; callback is the hackathon-ready receive path.

Only call numbers that consent (your phone / teammates). PTA + Uplift terms forbid spam.

## Key routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/sessions/create` | Uplift createSession (demo fallback if no key) |
| POST | `/api/sessions/call` | Outbound PSTN call via Uplift (`to` = PK mobile) |
| GET | `/api/sessions/calls` | Poll recent call / session states |
| POST | `/api/sessions/twilio-webhook` | Inbound Twilio → Uplift callback TwiML |
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
