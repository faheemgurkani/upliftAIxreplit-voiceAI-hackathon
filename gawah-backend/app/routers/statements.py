from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.db.database import Database, get_db
from app.models.statement import ReviewPayload
from app.services.edge_cases import handle_callback_lookup_allowed_fields
from app.services.pdf_service import PDFService, get_pdf_service

router = APIRouter(prefix="/api/statements", tags=["statements"])


@router.get("/{ref_code}")
async def get_statement(
    ref_code: str,
    full: bool = Query(True),
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    stmt = db.get_statement_by_ref(ref_code)
    if stmt is None:
        raise HTTPException(status_code=404, detail="Reference code not found")

    if not full:
        # Callback-safe limited disclosure
        allowed = set(handle_callback_lookup_allowed_fields())
        data = stmt.model_dump(mode="json")
        return {k: data.get(k) for k in allowed}

    return stmt.to_api_detail()


@router.post("/{ref_code}/review")
async def review_statement(
    ref_code: str,
    payload: ReviewPayload,
    db: Database = Depends(get_db),
) -> Dict[str, Any]:
    updated = db.review_statement(
        ref_code,
        reviewed_by=payload.reviewed_by,
        reviewer_notes=payload.reviewer_notes,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Reference code not found")
    db.record_kpi_event("statement_reviewed", {"ref_code": ref_code})
    return updated.to_api_detail()


@router.get("/{ref_code}/audio")
async def get_readback_audio(
    ref_code: str,
    db: Database = Depends(get_db),
):
    stmt = db.get_statement_by_ref(ref_code)
    if stmt is None:
        raise HTTPException(status_code=404, detail="Reference code not found")
    if not stmt.readback_audio_url:
        raise HTTPException(status_code=404, detail="Readback audio not available")

    path = Path(stmt.readback_audio_url)
    if not path.exists():
        # try local convention
        from app.config import get_settings

        alt = Path(get_settings().local_audio_dir) / stmt.ref_code / "readback.mp3"
        if alt.exists():
            path = alt
        else:
            raise HTTPException(status_code=404, detail="Audio file missing on disk")

    return FileResponse(path, media_type="audio/mpeg", filename=f"{ref_code}-readback.mp3")


@router.get("/{ref_code}/protection-pdf")
async def get_protection_referral_pdf(
    ref_code: str,
    db: Database = Depends(get_db),
):
    stmt = db.get_statement_by_ref(ref_code)
    if stmt is None:
        raise HTTPException(status_code=404, detail="Reference code not found")
    if not stmt.protection_referral_generated:
        raise HTTPException(status_code=404, detail="Protection referral not generated")

    path = Path(stmt.protection_referral_url) if stmt.protection_referral_url else None
    if path is None or not path.exists():
        from app.config import get_settings

        alt = Path(get_settings().local_audio_dir) / stmt.ref_code / "protection_referral.pdf"
        if alt.exists():
            path = alt
        else:
            raise HTTPException(status_code=404, detail="Protection PDF missing on disk")

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{ref_code}-protection-referral.pdf",
    )


@router.post("/{ref_code}/pdf")
async def generate_pdf(
    ref_code: str,
    db: Database = Depends(get_db),
    pdf: PDFService = Depends(get_pdf_service),
):
    stmt = db.get_statement_by_ref(ref_code)
    if stmt is None:
        raise HTTPException(status_code=404, detail="Reference code not found")
    content = pdf.generate_statement_pdf(stmt)
    from fastapi.responses import Response

    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="gawah-{ref_code}.pdf"'
        },
    )
