from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.db.database import Database, get_db
from app.services.kpi_service import compute_kpis

router = APIRouter(prefix="/api", tags=["kpis"])


@router.get("/kpis")
async def get_kpis(db: Database = Depends(get_db)) -> Dict[str, Any]:
    return compute_kpis(db)
