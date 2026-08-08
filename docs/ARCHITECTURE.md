# Architecture

> High-level system design — update as the stack and idea firm up.

## Overview

```text
[Witness phone] --> [Vapi] --> [Uplift Orator STT/TTS]
                         |
                         v
              [gawah-backend FastAPI]
                         |
         +---------------+---------------+
         v               v               v
   [OpenAI LLM]   [Supabase/JSON]   [PDF / ReportLab]
         |
         v
 [Next.js officer dashboard]
```

## Components

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `gawah-backend/` | Vapi webhooks, LLM structure, PDF, cases | Implemented |
| `client/` | Officer dashboard | Placeholder |
| `shared/` | Shared types & constants | Placeholder |

## Data flow

1. Witness calls Vapi assistant (language selected).
2. Orator/Vapi sends transcript webhooks to `/vapi/webhook` or `/vapi/transcript`.
3. LLM structures the account + flags inconsistencies.
4. Backend returns readback text; Vapi speaks it for confirmation.
5. Officer dashboard fetches `/statements/{case_id}` and downloads PDF.

## Key decisions

- STT / call orchestration: Vapi + Uplift Orator
- LLM: OpenAI `gpt-4o` (heuristic fallback without key)
- PDF: ReportLab FIR-style printable
- DB: Supabase or local JSON
- Backend host: Railway preferred; Vercel Python supported

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Latency | Stream responses; keep prompts short |
| Mic permissions | Clear UI copy + fallback text input |
| API limits | Cache where safe; demos use short sessions |
