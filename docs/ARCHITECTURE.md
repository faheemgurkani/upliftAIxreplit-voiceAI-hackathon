# Architecture

> High-level system design — update as the stack and idea firm up.

## Overview

```text
[Client / Voice UI]
        |
        v
[Server / API]
        |
        +--> [STT / ASR]
        +--> [LLM / Agent]
        +--> [TTS]
        +--> [Optional DB / Storage]
```

## Components

| Component | Responsibility | Status |
|-----------|----------------|--------|
| `client/` | UI, mic capture, playback | Placeholder |
| `server/` | API, orchestration, auth | Placeholder |
| `shared/` | Shared types & constants | Placeholder |

## Data flow

1. User speaks into the client.
2. Audio (or transcript) is sent to the server.
3. Server runs STT → reasoning → TTS (or streams responses).
4. Client plays / displays the response.

## Key decisions

- STT provider: _TBD_
- LLM / agent: _TBD_
- TTS provider: _TBD_
- Hosting: _TBD_ (e.g. Replit)

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Latency | Stream responses; keep prompts short |
| Mic permissions | Clear UI copy + fallback text input |
| API limits | Cache where safe; demos use short sessions |
