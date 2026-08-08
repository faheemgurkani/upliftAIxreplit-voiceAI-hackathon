# Gawah Client

Next.js 14 App Router dashboard for NGO/lawyer review of Gawah witness statements.

## Setup

```bash
cd client
cp .env.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). FastAPI should be running at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

## Routes

| Path | Purpose |
|------|---------|
| `/` | Landing |
| `/demo` | Browser voice session (`POST /api/sessions/create`) |
| `/dashboard` | Statement list |
| `/dashboard/[refCode]` | Statement detail + review |
| `/clusters` | Incident clusters |
| `/clusters/[clusterId]` | Corroboration map |

## Stack

- Next.js 14 + TypeScript + Tailwind CSS
- Fraunces + DM Sans
- `@upliftai/assistants-react` for live demo sessions (falls back to mock UI)
