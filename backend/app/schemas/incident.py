"""
NexusOps AI — Incident Pydantic Schemas
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    description: str | None = None
    severity: str = "medium"
    source: str = "manual"
    cluster_id: str | None = None
    cluster_name: str | None = None
    namespace: str | None = None
    affected_workload: str | None = None
    tags: list[str] | None = None


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    assignee: str | None = None
    root_cause: str | None = None
    remediation_steps: dict[str, Any] | None = None


class IncidentOut(BaseModel):
    id: str
    title: str
    description: str | None
    severity: str
    status: str
    source: str
    cluster_id: str | None
    cluster_name: str | None
    namespace: str | None
    affected_workload: str | None
    root_cause: str | None
    ai_confidence: float | None
    remediation_applied: bool
    alert_count: int
    assignee: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentAnalysisRequest(BaseModel):
    incident_id: str
    query: str = Field(..., min_length=10, max_length=2000)
    context_window_minutes: int = Field(default=60, ge=5, le=1440)
    include_logs: bool = True
    include_metrics: bool = True
    include_events: bool = True


class IncidentAnalysisOut(BaseModel):
    id: str
    incident_id: str
    query: str
    analysis: str
    root_cause_summary: str | None
    remediation_yaml: str | None
    confidence_score: float | None
    tokens_used: int | None
    llm_model: str | None
    context_sources: list[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AIInvestigateRequest(BaseModel):
    cluster_id: str
    query: str = Field(..., min_length=10, max_length=2000)
    context_window_minutes: int = Field(default=60, ge=5, le=1440)
    namespace: str | None = None
    workload: str | None = None


class AIInvestigateResponse(BaseModel):
    incident_id: str | None
    severity: str
    root_cause: str
    contributing_factors: list[str]
    remediation: dict[str, str]
    confidence: float
    analysis_detail: str
    tokens_used: int | None


class IncidentListResponse(BaseModel):
    items: list[IncidentOut]
    total: int
    page: int
    page_size: int
