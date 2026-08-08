from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class FieldCorroboration(BaseModel):
    field: str
    status: str = "single"
    agreement_score: Optional[float] = None
    values: List[Any] = Field(default_factory=list)
    conflict_detail: Optional[str] = None
    explainable: Optional[bool] = None
    explanation: Optional[str] = None
    note: Optional[str] = None


class IncidentCluster(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    cluster_label: Optional[str] = None
    incident_date_range: Optional[str] = None
    incident_location: Optional[str] = None
    statement_count: int = 0
    consensus_summary: Dict[str, Any] = Field(default_factory=dict)
    conflict_map: List[Dict[str, Any]] = Field(default_factory=list)
    cluster_status: str = "open"
    composite_score: Optional[float] = None
    collusion_warning: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_summary(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "cluster_label": self.cluster_label,
            "statement_count": self.statement_count,
            "composite_score": self.composite_score,
            "cluster_status": self.cluster_status,
            "incident_date_range": self.incident_date_range,
            "created_at": self.created_at.isoformat()
            if isinstance(self.created_at, datetime)
            else self.created_at,
            "collusion_warning": self.collusion_warning,
        }

    def to_detail(self, linked: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary = self.to_summary()
        consensus = self.consensus_summary or {}
        summary.update(
            {
                "field_results": self.conflict_map,
                "consensus_recommendation": consensus.get("recommendation"),
                "linked_statements": linked,
                "statements": linked,
                "consensus_summary": consensus,
            }
        )
        return summary
