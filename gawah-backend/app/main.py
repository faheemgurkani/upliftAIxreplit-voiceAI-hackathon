from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.db.database import get_db
from app.routers import cases, statements, vapi


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Eager-init DB / local store so first request is fast.
    get_db()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Gawah backend — multilingual voice witness statements for Pakistan policing demos.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vapi.router)
app.include_router(statements.router)
app.include_router(cases.router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": __version__,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    db = get_db()
    return {
        "status": "healthy",
        "env": settings.app_env,
        "db_backend": db.backend,
        "llm_enabled": settings.llm_enabled,
        "orator_configured": bool(settings.uplift_orator_key),
    }
