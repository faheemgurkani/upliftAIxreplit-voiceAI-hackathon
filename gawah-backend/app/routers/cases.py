from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.db.database import Database, get_db
from app.models.case import CaseCreate, CaseRecord, CaseStatusResponse
from app.services.statement_builder import generate_case_id, spoken_case_status

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("/create", response_model=CaseRecord)
async def create_case(
    payload: CaseCreate,
    db: Database = Depends(get_db),
) -> CaseRecord:
    case_id = payload.case_id or generate_case_id(payload.station_id)
    if db.get_case(case_id) is not None:
        raise HTTPException(status_code=409, detail="Case already exists")
    return db.create_case(payload, case_id=case_id)


@router.get("/{case_id}/status", response_model=CaseStatusResponse)
async def get_case_status(
    case_id: str,
    db: Database = Depends(get_db),
) -> CaseStatusResponse:
    record = db.get_case(case_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Case not found")

    return CaseStatusResponse(
        case_id=record.case_id,
        status=record.status,
        spoken_status=spoken_case_status(record.case_id, record.status, record.title),
        station_id=record.station_id,
        title=record.title,
    )


@router.get("/{case_id}", response_model=CaseRecord)
async def get_case(
    case_id: str,
    db: Database = Depends(get_db),
) -> CaseRecord:
    record = db.get_case(case_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return record
