# Gawah — Backend PRD for Next.js Frontend Design

**Audience:** Frontend / product design (Next.js App Router)  
**Backend:** FastAPI at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`)  
**Interactive API docs:** `http://localhost:8000/docs`  
**Status:** Hackathon MVP — live-tested with Uplift AI + OpenRouter  
**Auth:** None yet (open NGO demo dashboard; add later)

This document is the contract for designing and wiring the Next.js UI. When you bring a frontend template, connect it to these endpoints and shapes.

---

## 1. Product one-liner

**Gawah (گواہ)** lets witnesses in Pakistan give a legally structured statement by voice (Urdu / Punjabi), get it read back for confirmation, receive a 6-character reference code, and lets NGO/lawyer staff review statements, inconsistencies, protection referrals, and multi-witness corroboration on a dashboard.

---

## 2. User roles (frontend surfaces)

| Role | Primary UI | Goal |
|---|---|---|
| **Witness** | `/demo` (browser voice) or phone | Speak statement → hear readback → confirm → get ref code |
| **NGO / Lawyer / Officer** | `/dashboard`, `/clusters` | Review, escalate, prepare counsel, export |
| **Demo operator / judge** | Landing + KPIs | Show end-to-end story in 3–5 minutes |

No login in MVP. Treat dashboard as trusted local/demo access.

---

## 3. Screens the frontend must cover

| Route | Purpose | Backend deps |
|---|---|---|
| `/` | Brand landing + CTAs (Demo, Dashboard) | Optional `/health` |
| `/demo` | Start Uplift voice session; show connection + tool activity | `POST /api/sessions/create` (+ `@upliftai/assistants-react` if available) |
| `/dashboard` | Filterable statement list + KPI strip | `GET /api/dashboard/statements`, `GET /api/kpis` |
| `/dashboard/[refCode]` | Full statement detail | `GET /api/statements/{ref}`, review, audio, protection, inconsistencies |
| `/clusters` | Incident cluster list | `GET /api/dashboard/clusters` |
| `/clusters/[clusterId]` | Field-level corroboration map | `GET /api/dashboard/clusters/{id}` |

Optional later: `/lookup` public status by ref code (limited fields).

---

## 4. System architecture (what frontend talks to)

```text
[Next.js UI]
    |  fetch JSON / audio
    v
[FastAPI gawah-backend :8000]
    |-- Uplift AI (Realtime Assistants, TTS)   Singapore base URL
    |-- OpenRouter (DeepSeek V4 Flash)        structuring / engines
    |-- Local JSON store (MVP) or Supabase
```

**Frontend never holds** `UPLIFTAI_API_KEY` or `OPENROUTER_API_KEY`. Only `NEXT_PUBLIC_API_URL`.

---

## 5. Feature catalog (backend → UI mapping)

### 5.1 Voice demo session
- **Backend:** `POST /api/sessions/create` → `{ token, wsUrl, roomName, demo? }`
- **UI:** “Start voice session” → connect WebRTC room → mic on → show live status
- **Tools** (agent → backend, usually not called by UI directly): save statement, flag inconsistency/intimidation, privacy mode, protection assess, confirm
- **UI should show:** connecting / live / ended; last tool result if demo client simulates tools

### 5.2 Statement intake (5 legal fields)
Stored / displayed fields:

| Field | Key | Notes for UI |
|---|---|---|
| Time | `time_of_incident` | May be approximate; badge if `temporal_uncertainty` |
| Location | `location` | Required |
| Persons | `persons_present` | string[] |
| Sequence | `sequence_of_events` | Verbatim narrative (may be long, RTL for ur/pa) |
| Relationship | `relationship_to_accused` / `relationship_to_parties` | Optional |

Also show: `witness_type`, `language_of_call` (`ur` \| `pa` \| `ps` \| `mixed`), `ref_code`, `status`.

### 5.3 Reference code
- 6 chars, unambiguous alphabet (`A–Z` minus O/I, digits minus 0/1)
- Shown large after save/confirm; used as URL param `/dashboard/[refCode]`

### 5.4 Readback audio
- `GET /api/statements/{refCode}/audio` → `audio/mpeg`
- UI: `<audio controls src={getStatementAudioUrl(ref)} />`
- Also show `readback_text` as transcript

### 5.5 Witness confirmation
- Backend tool `confirm_statement` sets `confirmed_by_witness`
- UI badge: Confirmed / Not confirmed  
- **Do not** show signature/thumbprint UI (by design / CrPC §162)

### 5.6 Privacy mode
- `privacy_mode: true` → badge “Anonymous”; hide/avoid collecting name/address in UI copy

### 5.7 Intimidation / urgent escalation
- `intimidation_flag`, `status: urgent_escalation`
- UI: red **URGENT** badge; pin to top of list filter `flags=intimidation`

### 5.8 Inconsistency panel (Section 16)
- `inconsistency_flags[]` with:
  - `contradiction_type` / `category` (`temporal`, `spatial`, `identity`, `sequence`, `sensory`, `numerical`, …)
  - `segment_a`, `segment_b`
  - `analysis` / `contradiction_description`
  - `score` / `hybrid_score`
  - `legal_risk`, `source` (`realtime` \| `post_call_analysis`)
- UI: side-by-side A/B quotes + type chip + score

### 5.9 Witness protection
- `protection` / `protection_referral`:
  - `status`: `none` \| `referral_generated` \| `submitted`
  - `applicable_act`, `grounds[]`, `referral_pdf_url`
- UI section only when referral generated or intimidation/serious offence

### 5.10 Multi-witness corroboration (Section 17)
- Cluster list + detail with `field_results[]`:
  - `field`, `status` (`agreement` \| `partial_agreement` \| `conflict` \| `collusion_warning` \| …)
  - `agreement_score` 0–1
  - `values`, `conflict_detail`, `note`
- **Mandatory disclaimer everywhere scores appear:**  
  *“Pre-litigation intelligence only — not admissible corroboration under CrPC Section 162.”*
- Yellow badge on `collusion_warning`

### 5.11 NGO review workflow
- `POST /api/statements/{ref}/review` body `{ reviewed_by, reviewer_notes }`
- Sets `status: reviewed`
- UI form on detail page

### 5.12 KPIs / demo metrics
- `GET /api/kpis` → totals, urgent, clusters, avg corroboration, `edge_case_coverage`, `roi_proxies`
- UI: compact strip on dashboard (not on marketing hero)

### 5.13 PDF export
- `POST /api/statements/{ref}/pdf` → PDF download  
- Button on detail: “Download printable statement”

---

## 6. API reference (frontend-facing)

Base URL: `process.env.NEXT_PUBLIC_API_URL`  
CORS allows `http://localhost:3000` by default.

### 6.1 Health
```http
GET /health
```
```json
{
  "status": "healthy",
  "db_backend": "local_json",
  "uplift_configured": true,
  "openrouter_configured": true,
  "openrouter_model": "deepseek/deepseek-v4-flash-0731",
  "llm_enabled": true
}
```

### 6.2 Create voice session
```http
POST /api/sessions/create
Content-Type: application/json

{ "participantName": "Witness" }
```
```json
{
  "token": "...",
  "wsUrl": "wss://...",
  "ws_url": "wss://...",
  "roomName": "...",
  "room_name": "...",
  "demo": false,
  "ok": true
}
```
Use `token` + `wsUrl` with Uplift React SDK (`UpliftAIRoom`).

### 6.3 List statements
```http
GET /api/dashboard/statements?page=1&status=pending_review&flags=intimidation
```
Query:
- `page` (int, default 1)
- `status` optional: `pending_review` \| `urgent_escalation` \| `reviewed` \| `submitted` \| `incomplete` \| `archived`
- `flags` optional: `intimidation` \| `inconsistency`

```json
{
  "items": [
    {
      "ref_code": "X5QB2H",
      "created_at": "2026-08-08T10:00:00+00:00",
      "location": "Mohalla Hussain Abad Rawalpindi",
      "status": "urgent_escalation",
      "intimidation_flag": true,
      "inconsistency_flags": [],
      "corroboration_score": 0.71,
      "incident_cluster_id": "uuid",
      "privacy_mode": true,
      "language_of_call": "ur",
      "witness_type": "eyewitness"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

### 6.4 Statement detail
```http
GET /api/statements/{refCode}
```
Returns full object including:
- Core fields + `core_fields` mirror
- `inconsistency_flags`
- `protection` / `protection_referral`
- `corroboration_score`, `corroboration_detail`
- `readback_text`, `readback_audio_url`
- `confirmed_by_witness`, review fields

Limited callback-safe view (optional): `?full=false` → only `ref_code`, `status`, `created_at`, `location`, `time_of_incident`.

### 6.5 Review
```http
POST /api/statements/{refCode}/review
{ "reviewed_by": "NGO Lawyer", "reviewer_notes": "Ready for counsel" }
```

### 6.6 Audio
```http
GET /api/statements/{refCode}/audio
→ audio/mpeg
```

### 6.7 PDF
```http
POST /api/statements/{refCode}/pdf
→ application/pdf
```

### 6.8 Clusters
```http
GET /api/dashboard/clusters
→ { "items": [ { "id", "cluster_label", "statement_count", "composite_score", "collusion_warning", ... } ] }

GET /api/dashboard/clusters/{clusterId}
→ {
  "id", "cluster_label", "statement_count", "composite_score",
  "field_results": [...],
  "consensus_recommendation": "...",
  "linked_statements": [...],
  "collusion_warning": false
}
```

### 6.9 KPIs
```http
GET /api/kpis
```
(also mirrored at `GET /api/dashboard/kpis`)

### 6.10 Tool endpoints (agent / advanced demo)
Normally invoked by the voice agent, not the dashboard. Useful for scripted demos:

| Method | Path |
|---|---|
| POST | `/api/tools/save_witness_statement` |
| POST | `/api/tools/flag_inconsistency` |
| POST | `/api/tools/flag_intimidation` |
| POST | `/api/tools/enable_privacy_mode` |
| POST | `/api/tools/assess_protection_need` |
| POST | `/api/tools/confirm_statement` |

Common envelope:
```json
{
  "session_id": "room-or-session-id",
  "arguments": { "...tool fields..." }
}
```
Tool responses often include `{ "result": {...}, "presentationInstructions": "..." }` for the agent to speak.

### 6.11 Internal (not for public UI)
- `POST /api/internal/trigger-corroboration-analysis`
- `POST /api/internal/generate-protection-referral`

---

## 7. Status & badge design tokens (suggested)

| Status / flag | Badge | Color intent |
|---|---|---|
| `pending_review` | Pending | Amber |
| `urgent_escalation` | Urgent | Red |
| `reviewed` | Reviewed | Green/teal |
| `incomplete` | Incomplete | Gray |
| `intimidation_flag` | Threatened | Red outline |
| `inconsistency_flags.length > 0` | Flagged | Orange |
| `privacy_mode` | Anonymous | Slate |
| `corroboration_score >= 0.7` | Corroborated* | Green |
| `corroboration_score < 0.4` | Conflicting* | Amber |
| `collusion_warning` | Collusion check | Yellow |

\*Always with §162 disclaimer.

Language chips: `ur` → Urdu, `pa` → Punjabi, `ps` → Pashto (limited), `mixed` → Mixed.

RTL: for `ur` / `pa` / `ps` narrative blocks use `dir="rtl"`.

---

## 8. End-to-end demo flow (frontend choreography)

1. Landing → **Start demo**
2. `/demo` → `createSession` → connect Uplift room
3. Agent runs Phase 0–4 (voice); tools hit backend
4. On save: note `refCode` from tool result / poll dashboard
5. Open `/dashboard/{refCode}` → play readback → show flags/protection
6. Open linked `/clusters/{id}` → show corroboration map + disclaimer
7. Mark reviewed → show KPI strip update

Fallback if WebRTC SDK unavailable: button that calls `createSession` and displays token/wsUrl + “connected (mock)” while you seed tools via REST for the demo.

---

## 9. TypeScript contracts (copy into frontend)

Prefer keeping these in `lib/types.ts` / `lib/api.ts` (already sketched under `client/`).

Critical types:
- `StatementStatus`
- `StatementSummary` / `StatementDetail`
- `InconsistencyFlag`
- `ProtectionReferral`
- `ClusterSummary` / `ClusterDetail` / `FieldCorroboration`
- `KpiResponse`
- `SessionCreateResponse`
- `ReviewPayload`

Fetch helper rules:
- `cache: "no-store"` for dashboard data
- Throw on non-2xx with `detail` from FastAPI
- Encode `refCode` in URLs

---

## 10. Env for frontend template

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Backend (not in Next public env): Uplift + OpenRouter keys live in root / `gawah-backend` `.env`.

---

## 11. Error handling (UI)

| Situation | UX |
|---|---|
| Backend down | Banner from `/health` failure |
| 404 statement | “Reference code not found” |
| 404 audio | Hide player / “Readback audio not ready” |
| Session create fails | Show error; allow retry |
| `demo: true` session | Badge “Offline demo session” (no real Uplift) |
| Empty dashboard | Empty state + link to Demo |

---

## 12. Edge cases the UI should respect

| Edge case | UI behavior |
|---|---|
| Approximate time | Show verbatim; “approximate” chip if `temporal_uncertainty` |
| Delay > 30 days | Warning chip (`delayed_statement_high_risk`) |
| Privacy mode | No name/address fields; anonymous badge |
| Intimidation | Urgent styling; protection panel |
| Incomplete call | Status incomplete; show `call_phase_at_disconnect` if present |
| Pashto | Honest “limited support” copy — don’t fake full Pashto UX |
| Joint statement | Copy: separate session / separate ref code per speaker |
| Collusion warning | Yellow warning, not “perfect agreement” celebration |
| §162 scores | Always disclaimer; never “court corroboration” |

---

## 13. What NOT to build in frontend (MVP)

- Login / Supabase Auth (deferred)
- Thumbprint / e-sign capture
- Claiming PDPA compliance (see `COMPLIANCE_FUTURE_WORK.md`)
- Editing witness narrative as “truth” without audit (review notes only)
- Showing full statement on unverified public callback lookup

---

## 14. Local run checklist (for integration day)

```bash
# Terminal A — backend
source .venv/bin/activate
.venv/bin/uvicorn app.main:app --app-dir gawah-backend --reload --port 8000

# Terminal B — frontend
cd client   # or your new template folder
# set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Verify: `http://localhost:8000/health` then hit dashboard pages.

---

## 15. Existing client scaffold

There is already a Next.js scaffold under `client/` with routes and API helpers aligned to this PRD. When you provide a new template, we will:

1. Map template screens → routes above  
2. Reuse / port `lib/api.ts` + `lib/types.ts`  
3. Wire env + CORS  
4. Keep visual system from your template; keep data contracts from this PRD  

---

## 16. Glossary

| Term | Meaning |
|---|---|
| Ref code | 6-char public reference (e.g. `X5QB2H`) |
| Readback | Structured statement spoken/played back for confirmation |
| Cluster | Group of statements about the same incident |
| Corroboration score | Pre-litigation agreement score across witnesses |
| Protection referral | Suggested provincial/federal witness-protection pathway |

---

*PRD generated from the implemented FastAPI backend (Gawah hackathon MVP). For live OpenAPI schemas always prefer `/docs`.*
