from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.db.database import Database, get_db
from app.services.consistency_engine import run_consistency_check
from app.services.corroboration_engine import run_corroboration_analysis
from app.services.protection_service import generate_protection_referral_pdf

router = APIRouter(prefix="/api/internal", tags=["internal"])


class CorroborationTrigger(BaseModel):
    refCode: Optional[str] = None
    ref_code: Optional[str] = None
    sessionId: Optional[str] = None


class ProtectionTrigger(BaseModel):
    sessionId: Optional[str] = None
    ref_code: Optional[str] = None
    act: str


@router.post("/trigger-corroboration-analysis")
async def trigger_corroboration(
    payload: CorroborationTrigger,
    background: BackgroundTasks,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    ref = payload.refCode or payload.ref_code
    if not ref and payload.sessionId:
        stmt = db.get_statement_by_session(payload.sessionId)
        ref = stmt.ref_code if stmt else None
    if not ref:
        raise HTTPException(status_code=400, detail="refCode required")

    background.add_task(run_consistency_check, ref)
    background.add_task(run_corroboration_analysis, ref)
    return {"ok": True, "queued": True, "ref_code": ref}


@router.post("/generate-protection-referral")
async def generate_protection_referral(
    payload: ProtectionTrigger,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    stmt = None
    if payload.ref_code:
        stmt = db.get_statement_by_ref(payload.ref_code)
    elif payload.sessionId:
        stmt = db.get_statement_by_session(payload.sessionId)
    if stmt is None:
        raise HTTPException(status_code=404, detail="Statement not found")

    path = generate_protection_referral_pdf(stmt, payload.act)
    stmt.protection_referral_generated = True
    stmt.applicable_protection_act = payload.act
    stmt.protection_referral_url = path
    db.save_statement(stmt)
    return {"ok": True, "referral_pdf_url": path, "ref_code": stmt.ref_code}
