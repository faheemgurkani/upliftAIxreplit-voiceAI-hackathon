from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.db.database import Database, get_db
from app.models.statement import (
    GeneratePdfRequest,
    StatementConfirmRequest,
    StatementListResponse,
    StatementRecord,
)
from app.services.pdf_service import PDFService, get_pdf_service

router = APIRouter(prefix="/statements", tags=["statements"])


@router.get("/list", response_model=StatementListResponse)
async def list_statements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Database = Depends(get_db),
) -> StatementListResponse:
    items, total = db.list_statements(page=page, page_size=page_size)
    return StatementListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/generate-pdf")
async def generate_pdf(
    payload: GeneratePdfRequest,
    db: Database = Depends(get_db),
    pdf: PDFService = Depends(get_pdf_service),
) -> Response:
    statement: StatementRecord | None = None
    if payload.statement_id:
        statement = db.get_statement_by_id(payload.statement_id)
    elif payload.case_id:
        statement = db.get_statement_by_case(payload.case_id)
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide statement_id or case_id",
        )

    if statement is None:
        raise HTTPException(status_code=404, detail="Statement not found")

    pdf_bytes = pdf.generate_statement_pdf(statement)
    filename = f"gawah-statement-{statement.case_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/by-id/{statement_id}", response_model=StatementRecord)
async def get_statement_by_id(
    statement_id: str,
    db: Database = Depends(get_db),
) -> StatementRecord:
    statement = db.get_statement_by_id(statement_id)
    if statement is None:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement


@router.put("/{statement_id}/confirm", response_model=StatementRecord)
async def confirm_statement(
    statement_id: str,
    payload: StatementConfirmRequest,
    db: Database = Depends(get_db),
) -> StatementRecord:
    statement = db.confirm_statement(statement_id, officer=True)
    if statement is None:
        raise HTTPException(status_code=404, detail="Statement not found")
    # Notes / officer_name reserved for future audit trail.
    _ = payload
    return statement


@router.get("/{case_id}", response_model=StatementRecord)
async def get_statement_by_case(
    case_id: str,
    db: Database = Depends(get_db),
) -> StatementRecord:
    statement = db.get_statement_by_case(case_id)
    if statement is None:
        raise HTTPException(status_code=404, detail="Statement not found for case")
    return statement
