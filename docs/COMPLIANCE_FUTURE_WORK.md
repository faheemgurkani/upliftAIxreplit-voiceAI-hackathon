# Compliance — Future Work & Integration

> **Status:** Not implemented in the hackathon MVP. Tracked for post-demo / production readiness.  
> **Last reviewed:** August 2026 (web research; not legal advice).

Gawah handles **voice recordings, witness identity (optional), offence narratives, and protection-sensitive data**. That puts it at the intersection of **criminal procedure**, **privacy / data protection**, **telecom consent**, and emerging **AI governance**. Below is the compliance map to integrate later.

---

## 1. What matters most (simple summary)

| Layer | What it is | Latest / preferred reference | Binding now? |
|---|---|---|---|
| **Criminal procedure** | How witness statements must be taken & used | **CrPC 1898 §§161–162** (and related case law); watch **CrPC Amendment Bill 2025/2026** reforms | **Yes** for legal product claims |
| **Privacy / personal data** | Consent, purpose limits, sensitive data, retention, breach notice | Prefer readiness for **Personal Data Protection Bill 2023** (draft; sometimes discussed as updated **PDPA 2025** draft). Until enacted, use **GDPR-style** practices as best-effort | **Draft only** (not yet enacted as of mid-2026) |
| **Interim cyber / privacy patchwork** | Electronic crime, spam, basic privacy | **PECA 2016** (esp. spamming / misuse); **Constitution Art. 14** privacy | Partially yes |
| **Telecom / calling** | Unsolicited calls, consent for automated outreach | **PTA** spam / unsolicited comms framework (incl. **Protection from Spam… Regulations, 2009** lineage) + modern **explicit consent** expectations for services | Yes for live PSTN/outbound |
| **AI policy (soft)** | Ethical AI, sandboxes, transparency | **National AI Policy 2025** (policy, not hard statute) | Guidance only |
| **Witness protection statutes** | Referral routing by province | Punjab WPA **2018**, Sindh **2013**, Balochistan **2016**, Federal **2017** | Yes when generating referrals |

**Prefer for future integration:** design Gawah against **CrPC §§161–162** (product truth) + **PDPB 2023 / forthcoming PDPA** readiness (data) + **PTA consent / anti-spam** (phone channel) + optional **GDPR alignment** as international baseline until Pakistan’s PDPA is enacted.

---

## 2. Nature of each compliance type

### A. Criminal-procedure compliance (product core)
- **Nature:** Evidentiary / investigative process compliance — not “privacy law,” but whether Gawah’s output is usable and honest under Pakistani criminal practice.
- **Version to target:** **Code of Criminal Procedure, 1898**, especially:
  - **§161** — oral examination; record as actually made (no précis).
  - **§162** — limits on use (contradiction / defence use); why voice confirmation beats thumbprint theatre.
- **Watch:** proposed **Criminal Procedure Amendment Bill 2025** / related **2026** amendment activity (~55 reforms under discussion) — re-check before production launch.
- **Future work:** formal legal review checklist; §164 Magistrate handoff path; IO attestation workflow.

### B. Personal data protection (primary future integration)
- **Nature:** Controllership duties over personal & sensitive data (voice, identity, location, offence details, minors, sexual-offence context).
- **Preferred version:** Align architecture to the latest published draft — **Personal Data Protection Bill, 2023** (cabinet-approved draft lineage). MoITT has also discussed an updated draft sometimes referred to as **Personal Data Protection Act 2025** — adopt whichever text is enacted; until then treat **PDPB 2023** as the design target and keep a GDPR-compatible control set.
- **Status (Aug 2026):** **Not enacted** — do not claim “PDPA-compliant” yet; claim “PDPB-ready / privacy-by-design.”
- **Future work:**
  - Lawful basis + recorded voluntariness consent artifacts
  - Purpose limitation & retention schedules for audio / transcripts
  - Sensitive-data handling (minors, sexual offences, intimidation flags)
  - Data subject access / deletion / correction APIs
  - Breach notification playbook (draft bill often cites ~72h style notice)
  - Processor agreements with Uplift / OpenRouter / hosting

### C. Telecom & outbound-call compliance
- **Nature:** Consent and anti-spam rules for calls/SMS that reach real numbers.
- **References:** PTA unsolicited / spam frameworks; PECA spam provisions for direct marketing; explicit-consent expectations for chargeable / automated services.
- **Future work:** DNCR checks, call-purpose disclosure, consent logs, rate limits, no cold spam calling, Pakistan-number-only outbound already implied by Uplift calling rules.

### D. AI governance (soft compliance)
- **Nature:** Policy / ethics — transparency, human oversight, auditability.
- **Version:** **National AI Policy 2025** (and any later National Data Governance drafts).
- **Future work:** model cards, human-in-the-loop for NGO review, audit logs for tool calls, clear “not a court record / not IO replacement” disclaimers.

### E. Sectoral witness-protection law
- Already partially modeled in product; keep acts updated per province. **Not a substitute** for privacy law.

---

## 3. Recommended “future integration” backlog

| Priority | Work item | Compliance anchor |
|---|---|---|
| P0 | Consent & voluntariness evidence pack (store Phase-0 yes/no + timestamp + audio clip) | CrPC voluntariness + PDPB consent |
| P0 | Retention / deletion jobs for `readback.mp3`, transcripts, incomplete calls | PDPB / GDPR-style |
| P0 | Outbound-call consent + purpose prompt + opt-out | PTA / PECA |
| P1 | Data Processing Agreements + vendor inventory (Uplift, OpenRouter, host, DB) | PDPB / GDPR |
| P1 | Sensitive-case auto-privacy (sexual offence / minor) enforcement tests | PDPB sensitive data + WPA |
| P1 | NGO dashboard RBAC + audit trail | PDPB security |
| P2 | Formal legal memo on §161 digital examination vs IO duties | CrPC |
| P2 | Re-check CrPC Amendment Bill 2025/2026 once enacted | CrPC reforms |
| P2 | Switch claims from “PDPB-ready” → “PDPA-compliant” only after enactment | PDPA |
| P3 | AI Policy 2025 transparency pack for judges/demo | Soft AI policy |

---

## 4. What the MVP deliberately does *not* claim

- Not a substitute for an Investigating Officer or a **§164** Magistrate statement.
- Not court-admissible corroboration under **§162** (dashboard scores are pre-litigation intelligence only).
- Not certified under an enacted Pakistan PDPA (because none is in force as of this review).
- Not PTA-certified for mass outbound campaigns.

---

## 5. Codebase hooks (where to integrate later)

| Area | Suggested location |
|---|---|
| Consent / retention config | `gawah-backend/app/config.py` + new `services/compliance_service.py` |
| Consent artifacts on save | `routers/tools.py` → `save_witness_statement` |
| Deletion / export APIs | new `routers/compliance.py` |
| Call consent gate | `routers/sessions.py` + Uplift `place_call` |
| Dashboard disclaimer / DPIA notes | `client/` statement + cluster views |
| Schema fields | `sql/schema.sql` → `consent_record`, `retention_until`, `lawful_basis` |

Placeholder module: `gawah-backend/app/services/compliance_service.py` (stub only).

---

## 6. Sources checked (Aug 2026)

- Personal Data Protection Bill / Act draft discussions (PDPB **2023**; MoITT update track sometimes called **2025**)
- Chambers / practice guides: Pakistan Data Protection & Privacy **2026**
- CrPC **1898** §§161–162; reports on **Criminal Procedure Amendment Bill 2025** / **2026** activity
- PTA spam / unsolicited communications framework; PECA **2016** spam provisions
- Pakistan **National AI Policy 2025** (policy guidance)

*This document is for engineering planning only and is not legal advice. Obtain counsel before production deployment or public legal claims.*
