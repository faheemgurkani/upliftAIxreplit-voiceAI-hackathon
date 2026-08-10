# Web call, live dialogue, and statement pipeline — Gawah

**Project:** Voice AI Enabled Orchestration Engine (Gawah) · **Voice:** Uplift AI

Current behaviour of the **Demo → Browser** path in `frontend/artifacts/gawah-frontend` and `gawah-backend`.

## Layout (`/demo` while live)

| Region | Content |
|--------|---------|
| Left | Call panel — status, StartAudio (browser unlock), Mic on/off, End call |
| Right | Live dialogue — Agent (ایجنٹ) / Witness (گواہ) bubbles |

The right panel **matches the call panel height** and **scrolls internally**. It must not grow the page as turns accumulate.

## Data sources

1. **Live captions** — LiveKit `useTranscriptions` + `useVoiceAssistant().agentTranscriptions` inside `UpliftAIRoom`.
2. **Witness mic** — continuous `MediaRecorder` for STT after hang-up.
3. **Agent voice** — Uplift TTS (`defense-advocate` by default); instructions force Nastaliq Urdu so caption text matches speech.

## End-of-call flow

1. User clicks **End call** → demo enters `processing` state (animated panel: upload → STT → §161 → dashboard). Live call UI stays mounted but hidden so the upload can finish.
2. Client stops recorder and posts multipart to `POST /api/sessions/web/{callId}/recording`.
3. Optional form field `dialogue`: JSON list of `{ role, text, id?, at? }`.
4. Backend (`web_call_pipeline.py`):
   - Saves audio under local audio dir
   - Runs Uplift STT → `witness_transcript`
   - Merges STT into dialogue if no live witness turns
   - Structures §161 fields from **witness-only** text
   - Persists statement + `ref_code`
   - Returns full `transcript`, `dialogue`, `witness_transcript`
5. Client calls `POST /api/sessions/web/{callId}/complete`.
6. Ended UI: “Processing complete” + CTAs (Open statement / Calls / Dashboard) + full dialogue chat.

## Do not

- Call client `updateInstruction()` with a short blurb — it **replaces** the full system prompt and kills Phase 0–4.
- Truncate transcript display for the ended screen.
- Rely on English/Roman agent text for captions — language lock is in `agent_instructions.txt` + greeting.

## Related files

| Area | Path |
|------|------|
| Live UI | `frontend/artifacts/gawah-frontend/src/components/live-web-call.tsx` |
| Chat UI | `…/components/transcript-chat.tsx` |
| Demo page | `…/pages/demo.tsx` |
| Upload API client | `…/lib/api.ts` (`uploadWebRecording`) |
| Pipeline | `gawah-backend/app/services/web_call_pipeline.py` |
| Adhoc config | `gawah-backend/app/services/uplift_service.py` |
| Prompts | `gawah-backend/app/prompts/` |
