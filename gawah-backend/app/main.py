from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.db.database import get_db
from app.routers import dashboard, internal, kpis, sessions, statements, tools


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_db()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "Gawah — CrPC §161 voice witness statements for Pakistan. "
        "Uplift AI realtime + Groq structuring + consistency/corroboration engines."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(tools.router)
app.include_router(statements.router)
app.include_router(dashboard.router)
app.include_router(internal.router)
app.include_router(kpis.router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": __version__,
        "status": "ok",
        "docs": "/docs",
        "stack": {
            "voice": "Uplift AI Realtime Assistants + TTS/STT",
            "llm": "Groq openai/gpt-oss-120b",
            "db": "Supabase or local JSON",
        },
    }


@app.get("/health")
async def health():
    db = get_db()
    return {
        "status": "healthy",
        "env": settings.app_env,
        "db_backend": db.backend,
        "uplift_configured": settings.uplift_enabled,
        "groq_configured": settings.groq_enabled,
        "llm_enabled": settings.llm_enabled,
        "assistant_id_set": bool(settings.uplift_assistant_id),
    }
