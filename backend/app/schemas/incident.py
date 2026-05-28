"""
NexusOps AI — Incident Pydantic Schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    description: Optional[str] = None
    severity: str = "medium"
    source: str = "manual"
    cluster_id: Optional[str] = None
    cluster_name: Optional[str] = None
    namespace: Optional[str] = None
    affected_workload: Optional[str] = None
    tags: Optional[List[str]] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    root_cause: Optional[str] = None
    remediation_steps: Optional[Dict[str, Any]] = None


class IncidentOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    severity: str
    status: str
    source: str
    cluster_id: Optional[str]
    cluster_name: Optional[str]
    namespace: Optional[str]
    affected_workload: Optional[str]
    root_cause: Optional[str]
    ai_confidence: Optional[float]
    remediation_applied: bool
    alert_count: int
    assignee: Optional[str]
    tags: Optional[List[str]]
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
    root_cause_summary: Optional[str]
    remediation_yaml: Optional[str]
    confidence_score: Optional[float]
    tokens_used: Optional[int]
    llm_model: Optional[str]
    context_sources: Optional[List[str]]
    created_at: datetime

    model_config = {"from_attributes": True}


class AIInvestigateRequest(BaseModel):
    cluster_id: str
    query: str = Field(..., min_length=10, max_length=2000)
    context_window_minutes: int = Field(default=60, ge=5, le=1440)
    namespace: Optional[str] = None
    workload: Optional[str] = None


class AIInvestigateResponse(BaseModel):
    incident_id: Optional[str]
    severity: str
    root_cause: str
    contributing_factors: List[str]
    remediation: Dict[str, str]
    confidence: float
    analysis_detail: str
    tokens_used: Optional[int]


class IncidentListResponse(BaseModel):
    items: List[IncidentOut]
    total: int
    page: int
    page_size: int
