# Uplift AI — Voice AI Hackathon Guide

Welcome to the **Uplift AI × Replit Voice AI Hackathon**! This guide has everything you need to build with Uplift AI: lifelike Urdu text-to-speech, and AI voice agents that make real phone calls.

Whatever your track — AI voice apps, AI media, creative AI etc — the two building blocks below (TTS and phone calls) are your starting point.

> **Tip: give this doc to your AI tools.** This guide is self-contained. Paste it into Replit Agent as context and ask it to build with the Uplift AI API — all the endpoints, examples, and error codes it needs are here.

---

## 1. Get your API key

1. Sign up at [upliftai.org](https://upliftai.org) — you get free credits on signup (plus extra hackathon credits of $50 from the organizers).
2. Go to **[upliftai.org/app/developer/api-keys](https://upliftai.org/app/developer/api-keys)**.
3. Click **Create API key** and copy the key.

> ⚠️ The key is shown **only once**. Save it somewhere safe (e.g. a Replit Secret). If you lose it, revoke it and create a new one.

---

## 2. Full documentation

This guide covers the essentials. The complete docs live at **[docs.upliftai.org](https://docs.upliftai.org)**:

- [Text-to-Speech API](https://docs.upliftai.org/orator) — full API reference
- [Voice library](https://docs.upliftai.org/orator_voices) — all voices with audio samples
- [WebSocket TTS](https://docs.upliftai.org/websocket-tts) — real-time streaming guide
- [Realtime Assistants](https://docs.upliftai.org/assistants/introduction) — voice agents, tools, React SDK
- [Node.js SDK](https://docs.upliftai.org/sdk/nodejs/overview) — optional typed SDK (`npm install @upliftai/sdk-js`)
- [Tutorials](https://docs.upliftai.org/tutorials) — WhatsApp bot, LiveKit voice agent, conversational AI

---

## 3. Text-to-speech (streaming)

Stream the audio instead of waiting for a complete file — playback starts as soon as the first chunk arrives. This is what you want for voice agents, conversational apps, and anything real-time.

### Quick start — HTTP streaming

```bash
curl -X POST https://api.upliftai.org/v1/synthesis/text-to-speech/stream \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  --no-buffer \
  -d '{
    "voiceId": "v_8eelc901",
    "text": "السلام علیکم! امید ہے آپ خیریت سے ہوں گے۔",
    "outputFormat": "MP3_22050_128"
  }' \
  --output audio.mp3
```

The response is a chunked audio stream — chunks arrive while synthesis is still running.

Same thing in JavaScript, consuming chunks as they arrive:

```js
const res = await fetch("https://api.upliftai.org/v1/synthesis/text-to-speech/stream", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.UPLIFTAI_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    voiceId: "v_8eelc901",
    text: "السلام علیکم! امید ہے آپ خیریت سے ہوں گے۔",
    outputFormat: "MP3_22050_128",
  }),
});

for await (const chunk of res.body) {
  // feed each chunk to your player / pipe to a file / forward to the browser
}
```

With the Node SDK this is [`client.tts.createStream()`](https://docs.upliftai.org/sdk/nodejs/text-to-speech-stream).

Some voices to try (full list with samples: [docs.upliftai.org/orator_voices](https://docs.upliftai.org/orator_voices)):

| Voice | `voiceId` | Style |
|---|---|---|
| Info/Education | `v_8eelc901` | Clear, informative |
| Nostalgic News | `v_30s70t3a` | Classic Pakistani news anchor |
| Dada Jee | `v_yypgzenx` | Storytelling, suspenseful |
| Gen Z | `v_kwmp7zxt` | Fast, contemporary |

### Lower latency from Pakistan — Singapore region 🇸🇬

Uplift AI runs in two regions. From Pakistan, the **Singapore** region is noticeably faster (shorter network round trip):

| Region | Base URL |
|---|---|
| US (default) | `https://api.upliftai.org/v1` |
| **Singapore — use this from Pakistan** | `https://ap-southeast-1.api.upliftai.org/v1` |

TTS works on both regions. **Phone calling works only on Singapore** — see section 4.

Same API, same endpoints, same API key — just swap the base URL:

```bash
curl -X POST https://ap-southeast-1.api.upliftai.org/v1/synthesis/text-to-speech/stream \
  -H "Authorization: Bearer YOUR_API_KEY" \
  ...
```

### WebSocket streaming (lowest latency, ~300 ms to first audio)

A persistent Socket.IO connection that multiplexes many synthesis requests — ideal for voice agents and live conversations:

```
US:        wss://api.upliftai.org/text-to-speech/multi-stream
Singapore: wss://ap-southeast-1.api.upliftai.org/text-to-speech/multi-stream
```

Authenticate by passing your API key as `token` in the Socket.IO `auth` object — the field must be named `token`, not `apiKey`:

```js
import { io } from "socket.io-client";

const socket = io("wss://ap-southeast-1.api.upliftai.org/text-to-speech/multi-stream", {
  auth: { token: process.env.UPLIFTAI_API_KEY },
});
```

Send `synthesize` messages (`text`, `voiceId`, `outputFormat`), receive base64 audio chunks. Full protocol + example code: [docs.upliftai.org/websocket-tts](https://docs.upliftai.org/websocket-tts).

### Output formats

`PCM_22050_16`, `WAV_22050_16`, `WAV_22050_32`, `MP3_22050_32`, `MP3_22050_64`, `MP3_22050_128`, `OGG_22050_16`, `ULAW_8000_8`

- Web playback: `MP3_22050_128` is a good default.
- Telephony integrations (e.g. your own SIP/WhatsApp voice pipeline): `ULAW_8000_8`.

### TTS errors

| Status | Meaning |
|---|---|
| 400 | Invalid request (bad `voiceId`, missing field, text too long — cap is 10,000 chars, ~2,000 for some voices) |
| 401 | Missing/invalid API key |
| 402 | Out of credits — top up, then retry (not permanent) |
| 429 | Rate limited — back off and retry |
| 500 | Server error — retry with backoff |

---

## 4. Make a phone call

Your assistant can call real Pakistani phone numbers. Two steps: create an assistant (once), then trigger calls to any number.

> ### ⚠️ Calling works ONLY on the Singapore endpoint
>
> Every calling request in this section — creating assistants, placing calls, checking call status — **must** use the Singapore base URL:
>
> ```
> https://ap-southeast-1.api.upliftai.org/v1
> ```
>
> Pakistani phone calls **cannot** be placed through the US endpoint (`api.upliftai.org`). If your call requests fail unexpectedly, first check you're on the Singapore URL.

### Step 1 — Create an assistant

An assistant is a saved voice-agent configuration: its instructions (personality + goal), voice, and models.

```bash
curl -X POST https://ap-southeast-1.api.upliftai.org/v1/realtime-assistants \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hackathon Caller",
    "config": {
      "agent": {
        "instructions": "You are a friendly assistant from a Lahore bakery. Remind the customer their cake order is ready for pickup today. Be warm and brief. Always respond in Urdu using nastaliq script.",
        "initialGreeting": true,
        "greetingInstructions": "سلام کریں اور اپنا تعارف کروائیں۔"
      },
      "stt": {
        "default": { "provider": "soniox", "model": "stt-rt-v4", "language": "ur" }
      },
      "tts": {
        "default": { "provider": "upliftai", "voiceId": "helpdesk-agent", "outputFormat": "MP3_22050_32" }
      },
      "llm": {
        "default": { "provider": "google", "model": "gemini-2.5-flash" }
      }
    }
  }'
```

This is the same model stack that powers the live calling demo on [upliftai.org](https://upliftai.org) — a solid default for Urdu calls.

The response includes `realtimeAssistantId` — save it. Full reference (tools, greeting options, web sessions, React SDK): [docs.upliftai.org/assistants](https://docs.upliftai.org/assistants/introduction).

### Step 2 — Call a number

```bash
curl -X POST https://ap-southeast-1.api.upliftai.org/v1/calls \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "assistantId": "YOUR_ASSISTANT_ID",
    "to": "+923001234567"
  }'
```

Response:

```json
{ "callId": "…", "status": "dispatched" }
```

**Request fields:**

| Field | Required | Notes |
|---|---|---|
| `assistantId` | yes | From step 1 |
| `to` | yes | E.164 (`+923001234567`) or local (`03001234567`). **Pakistani numbers only.** |
| `variables` | no | JSON object of per-call data (e.g. `{ "name": "Ahmed", "order": "chocolate cake" }`) available to the assistant. Max ~3,000 chars total, keys ≤ 64 chars. |
| `additionalInstructions` | no | Extra instructions appended to the assistant's prompt **for this call only** (max 2,000 chars). Great for per-call personalization without editing the assistant. |

Optional header: `Idempotency-Key: <any-string-≤256-chars>` — safe-retry protection. Sending the same key twice returns `409 {"error":"duplicate_in_flight"}` instead of dialing twice.

Calls go out from an Uplift AI Pakistani caller number automatically — you don't need to own a number.

### `dispatched` does NOT mean answered

`dispatched` only means the call was queued and dialing started. To see what actually happened, poll the session list:

```bash
curl "https://ap-southeast-1.api.upliftai.org/v1/realtime-assistants/YOUR_ASSISTANT_ID/sessions?limit=10" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Each session row has a `state` that progresses:

```
dispatched → dialing → ringing → answered → completed | failed
```

(Some carriers skip `dialing`/`ringing` and jump straight to `answered`.)

Failed calls include a `failureReason`:

| `failureReason` | Meaning | What to do |
|---|---|---|
| `busy` | Line busy | Retry later |
| `no_answer` | Rang, nobody picked up | Retry later |
| `silent_pickup` | Call "answered" but no audio from the callee — a phantom answer, common on Pakistani networks | Retry later; the number is usually fine |
| `voicemail` | Answering machine detected | Retry later |
| `silent_pickup` | Call connected but no one spoke (phantom answer / dead line) | Retry later |
| `declined` | Person rejected the call | Respect it |
| `wrong_number` | Number doesn't exist | Don't retry |
| `unreachable` | Phone off / no coverage | Don't retry immediately |
| `network_error` | Carrier fault, not the callee | Retry |
| `call_failed` | Anything else | Check your config, ask us |

Transcripts, recordings, and analysis are generated **asynchronously** after the call ends — they may take a minute to appear.

### Call error codes

| Status | Response / message | Meaning & fix |
|---|---|---|
| 400 | `"to must be E.164 (e.g., +14155551234) or local format (e.g., 03001234567)"` | Fix the number format |
| 400 | `"Invalid … outbound phone number …: Nayatel only supports Pakistani numbers"` | Only `+92` / `03…` numbers can be called |
| 400 | `"additionalInstructions must be shorter than or equal to 2000 characters"` (and similar) | Field validation — check the fields table above |
| 401 | `"invalid authorization"` / `"expired authorization"` / `"API Key has been revoked"` | Check your `Authorization: Bearer` header and key |
| 402 | `"Insufficient credits to start a realtime session"` | Out of credits — top up (ask organizers for hackathon credits), then retry |
| 404 | `"Realtime assistant not found: <id>"` | Wrong `assistantId` |
| 409 | `{"error": "number_busy", "callId": "…"}` | A live call to that number already exists — wait for it to finish |
| 409 | `{"error": "duplicate_in_flight", "callId": "…"}` | Same `Idempotency-Key` reused while the original call is in flight |
| **429** | `"Organization concurrent outbound call limit reached"` | **Concurrency limit — see below** |
| 429 | `"All outbound caller IDs at line capacity"` | Platform-wide line capacity is full — retry in a minute |
| 429 | `"ThrottlerException: Too Many Requests"` | API rate limit (150 requests/min) — slow down, honor `Retry-After` |
| 500 | `"Internal server error"` | Dial infrastructure hiccup — retry with backoff |

Distinguish the three 429s by the `message` string.

### Concurrency limits

By default each organization can have **1 outbound call in progress at a time**. Starting a second call while one is live returns:

```
429 { "statusCode": 429, "message": "Organization concurrent outbound call limit reached" }
```

- Wait for the current call to end (poll sessions for `completed`/`failed`), then dial the next.
- This limit **cannot be increased at the moment** — design your project around one call at a time (a simple queue works great).
- The general API rate limit is 150 requests/minute — plenty, as long as you don't poll in a tight loop.

### Responsible calling

Phone calls reach real people on real networks. Please use this only for calls people would welcome — demos to your own phone, your teammates, and consenting testers. Using automated calling for spam, harassment, or fraudulent purposes is against PTA (Pakistan Telecommunication Authority) regulations and Uplift AI's terms, and will get an org's calling access suspended. Keep it fun and keep it legal — we'd love to see what you build.

---

## 5. Tips

- **Use the Singapore base URL** (`ap-southeast-1.api.upliftai.org`) from Pakistan for everything — it noticeably cuts TTS latency.
- **Poll politely.** Check call status every 2–5 seconds, not in a tight loop.
- **Back off on 429.** Wait a few seconds and retry; don't hammer.
- **402 is temporary.** After topping up credits, just retry the same request.
- **Test on your own phone first.** Call yourself before calling anyone else — you'll hear exactly what your assistant sounds like and can tune instructions fast.
- **Iterate with `additionalInstructions`** for per-call tweaks instead of editing the assistant every time.
- Stuck? Find the Uplift AI team at the hackathon, or check [docs.upliftai.org](https://docs.upliftai.org).

Happy building! 🎙️🇵🇰
