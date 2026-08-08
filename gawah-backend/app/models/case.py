from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


CaseStatus = Literal["open", "in_progress", "statement_pending", "closed"]


class CaseCreate(BaseModel):
    station_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: CaseStatus = "open"
    case_id: Optional[str] = None


class CaseRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    status: CaseStatus = "open"
    station_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CaseStatusResponse(BaseModel):
    case_id: str
    status: CaseStatus
    spoken_status: str
    station_id: Optional[str] = None
    title: Optional[str] = None
