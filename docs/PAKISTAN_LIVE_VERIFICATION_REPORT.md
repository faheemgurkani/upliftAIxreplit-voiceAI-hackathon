# Pakistan Live Verification — Gawah (Voice AI Enabled Orchestration Engine)

**Project:** Voice AI Enabled Orchestration Engine (Gawah) · **Product:** Gawah  
**Origin:** Uplift AI × Replit Voice AI Hackathon (2026)

**Probe:** `gawah-backend/scripts/live_integration_test.py`  
**Result artifact:** `gawah-backend/data/live_probe_results.json`  
**Outcome:** **21 / 21 passed** (~6 minutes)  
**Stack verified:** Uplift AI (Singapore) + OpenRouter (`deepseek/deepseek-v4-flash-0731`) + local FastAPI  
**Region focus:** Pakistan criminal-justice / NGO demo context  
**Date context:** August 2026

> This is an engineering verification report mapped to Pakistan legal *product intent*. It is **not** a court certification and **not** legal advice.

---

## 1. Plain-language verdict

For a Pakistan hackathon MVP demo, the live stack works end-to-end:

- Urdu TTS readback (Uplift)
- Realtime assistant + WebRTC session tokens (Uplift Singapore)
- LLM structuring / analysis (OpenRouter DeepSeek)
- Statement save → ref code → confirm → NGO review
- Intimidation escalation + Punjab Witness Protection Act 2018 referral path
- Multi-witness cluster (2 statements, corroboration score ~0.57)
- Dashboard list/detail/KPIs + readback audio delivery

**Not verified in this probe:** incomplete-call recovery, live PSTN phone call to a real `+92` number, Supabase persistence, Twilio bridge.

---

## 2. Probe results → Pakistan meaning

| # | Probe | Pass detail (short) | Why it matters in Pakistan |
|---|---|---|---|
| 1 | `openrouter.direct` | DeepSeek JSON ping OK | Local LLM path for structuring / flagging without Groq |
| 2 | `uplift.tts` | `v_8eelc901` stream ~51KB | Urdu readback — witnesses can *hear* statement before confirm |
| 3 | `uplift.assistant.create` | Assistant created | Voice agent host for CrPC-style examination flow |
| 4 | `uplift.session.create` | `token` + `wsUrl` | Browser demo mode (no station visit) |
| 5 | `api.health` | Uplift + OpenRouter configured | Demo readiness gate |
| 6 | `api.sessions.create` | Real session (`demo=false`) | Frontend can start live voice |
| 7 | `api.tools.flag_intimidation` | Escalated | Threat/coercion → urgent NGO queue (common withdrawal driver) |
| 8 | `api.tools.save_witness_statement` | Ref `X5QB2H` + readback | §161-style capture + voice-accessible reference code |
| 9 | `api.llm.provider` | OpenRouter / DeepSeek Flash | Production LLM wiring for PK demo |
| 10 | `engine.consistency` | Ran (0 new post-call flags) | §162 risk surface scanner (realtime flag already present) |
| 11 | `api.tools.save_second_witness` | Ref `VHFBPU` | Second independent account (anti joint-statement practice) |
| 12 | `engine.corroboration` | Cluster n=2, score **0.568** | Pre-litigation multi-witness intel (not court corroboration) |
| 13 | `api.statements.detail` | Status pending; 1 flag | NGO detail view data OK |
| 14 | `api.tools.assess_protection_need` | **Punjab WPA 2018 — Unit II** | Provincial protection statute routing verified |
| 15 | `api.tools.confirm_statement` | Confirmed `X5QB2H` | Voice confirmation instead of thumbprint/sign (§162: statements not to be signed) |
| 16 | `api.dashboard.statements` | total=2 | Lawyer list view |
| 17 | `api.dashboard.clusters` | count=1 | Incident grouping UI |
| 18 | `api.dashboard.cluster_detail` | 2 linked statements | Field conflict map data |
| 19 | `api.kpis` | Edge coverage mostly true | Demo metrics for judges |
| 20 | `api.statements.audio` | 200, ~350KB | Playable Urdu readback evidence artifact |
| 21 | `api.statements.review` | `reviewed` | NGO human-in-the-loop closeout |

---

## 3. Pakistan legal anchors touched by this probe

### CrPC 1898 — Section 161
Oral examination / record of what the witness said. Gawah’s save + verbatim `sequence_of_events` + structured follow-up fields support this product model (digital intake for NGO/IO assistance — **not** a replacement IO).

### CrPC 1898 — Section 162
- Statements to police are **not to be signed**; primarily usable to **contradict** at trial.
- Gawah’s **voice confirmation** (probe #15) and **no thumbprint UX** align with this.
- Corroboration score (probe #12) must stay labeled **pre-litigation intelligence only**.

### Punjab Witness Protection Act 2018
Probe #14 returned Unit II (serious offences) when intimidation + serious assault were set — correct provincial routing for a Punjab-flavored demo.

### Language access (Pakistan)
Urdu TTS verified; KPI edge `language_access_ur_pa: true`. Pashto remains limited (by product design).

### Digital recording reality check (case-law context)
Public commentary / SC-linked guidance notes that digital recording may **corroborate investigation** but does **not** automatically replace a formal §161 written police record or a §164 Magistrate statement. MVP claim language must stay honest: *assistive digital examination + NGO workflow*, not “court-ready FIR substitute.”

---

## 4. KPI edge-case coverage (from probe #19)

| Edge flag | Result | Pakistan note |
|---|---|---|
| intimidation | ✅ | Threat → urgent path |
| privacy_mode | ✅ | Sensitive / anonymous witness |
| inconsistency_engine | ✅ | §162 contradiction surface |
| delay_doctrine | ✅ | Delay explanation / high-risk flag support |
| incomplete_call_recovery | ❌ not exercised | Mid-call hangup path still to demo |
| multi_witness_corroboration | ✅ | Neighbour/bystander clustering |
| language_access_ur_pa | ✅ | Urdu/Punjabi access story |
| protection_referral | ✅ | Punjab WPA path |

---

## 5. Demo script claims you can safely make

**Safe to say**
- Live Urdu TTS readback works on Uplift Singapore.
- Browser session tokens work for a voice demo.
- Statement gets a 6-char ref code; witness can confirm by voice path.
- Intimidation escalates; Punjab WPA 2018 referral text generates.
- Two witnesses can be clustered with a scored conflict/agreement map for lawyers.
- NGO can review and mark reviewed; audio is playable.

**Do not say**
- “This is a signed §161 police statement.”
- “Corroboration score is admissible in court.”
- “This replaces §164 Magistrate confession/statement.”
- “PDPA-certified” (Pakistan PDPA still draft — see `COMPLIANCE_FUTURE_WORK.md`).

---

## 6. Follow-ups for a stronger Pakistan demo

1. Place one real outbound call to a consenting `+92` test phone (Uplift Singapore `/calls`).
2. Exercise **incomplete** hangup path (`call_phase_at_disconnect`).
3. Seed a clearer post-call consistency contradiction so Layer-2 flags > 0.
4. Show Punjab vs Sindh protection act switching live.
5. Keep §162 disclaimer visible on cluster UI.

---

## 7. Raw artifact

Machine-readable results: [`gawah-backend/data/live_probe_results.json`](../gawah-backend/data/live_probe_results.json)

Related docs:
- [`BACKEND_PRD_FOR_FRONTEND.md`](./BACKEND_PRD_FOR_FRONTEND.md)
- [`COMPLIANCE_FUTURE_WORK.md`](./COMPLIANCE_FUTURE_WORK.md)
- [`FULL_SPEC_AND_IMPLEMENTATION_PLAN.md`](./FULL_SPEC_AND_IMPLEMENTATION_PLAN.md)
