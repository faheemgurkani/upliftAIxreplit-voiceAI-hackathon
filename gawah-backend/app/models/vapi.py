from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


WitnessLanguage = Literal["urdu", "punjabi", "pashto", "english"]


class VapiCallObject(BaseModel):
    id: Optional[str] = None
    status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VapiCallStartedPayload(BaseModel):
    call_id: str
    language: WitnessLanguage = "urdu"
    case_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VapiTranscriptPayload(BaseModel):
    call_id: str
    transcript: str
    language: WitnessLanguage = "urdu"
    case_id: Optional[str] = None
    role: Optional[str] = "user"
    is_final: bool = True


class VapiCallEndedPayload(BaseModel):
    call_id: str
    language: WitnessLanguage = "urdu"
    case_id: Optional[str] = None
    transcript: Optional[str] = None
    ended_reason: Optional[str] = None


class VapiConfirmationPayload(BaseModel):
    call_id: str
    case_id: Optional[str] = None
    confirmed: bool = True
    statement_id: Optional[str] = None


class VapiArtifact(BaseModel):
    transcript: Optional[str] = None
    messages: List[Dict[str, Any]] = Field(default_factory=list)


class VapiServerMessage(BaseModel):
    """Native Vapi server-url envelope: { \"message\": { ... } }."""

    type: str
    call: Optional[VapiCallObject] = None
    role: Optional[str] = None
    transcript: Optional[str] = None
    transcriptType: Optional[str] = None
    endedReason: Optional[str] = None
    artifact: Optional[VapiArtifact] = None
    functionCall: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VapiWebhookEnvelope(BaseModel):
    message: VapiServerMessage
