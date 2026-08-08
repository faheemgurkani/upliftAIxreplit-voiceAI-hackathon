from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


WitnessLanguage = Literal["urdu", "punjabi", "pashto", "english"]


class StructuredStatement(BaseModel):
    incident_date: str = ""
    incident_time: str = ""
    incident_location: str = ""
    persons_involved: List[str] = Field(default_factory=list)
    sequence_of_events: List[str] = Field(default_factory=list)
    witness_name: str = ""
    inconsistencies: List[str] = Field(default_factory=list)


class WitnessStatement(BaseModel):
    case_id: str
    witness_language: WitnessLanguage = "urdu"
    raw_transcript: str = ""
    structured_statement: Dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    call_sid: str = ""


class StatementRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    call_sid: Optional[str] = None
    witness_language: WitnessLanguage = "urdu"
    raw_transcript: str = ""
    structured_statement: StructuredStatement = Field(default_factory=StructuredStatement)
    inconsistencies: List[str] = Field(default_factory=list)
    confirmed: bool = False
    officer_confirmed: bool = False
    readback_text: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatementListResponse(BaseModel):
    items: List[StatementRecord]
    total: int
    page: int
    page_size: int


class GeneratePdfRequest(BaseModel):
    statement_id: Optional[str] = None
    case_id: Optional[str] = None


class StatementConfirmRequest(BaseModel):
    officer_name: Optional[str] = None
    notes: Optional[str] = None
