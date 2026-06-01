"""Pydantic schemas for AI incident investigations."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class InvestigationCreate(BaseModel):
    incident_id: str | None = None
    cluster_id: str | None = None
    title: str | None = None
    query: str = Field(..., min_length=10, max_length=3000)
    run_immediately: bool = True


class InvestigationOut(BaseModel):
    id: str
    incident_id: str | None
    cluster_id: str | None
    title: str
    query: str
    status: str
    summary: str | None
    root_cause: str | None
    root_cause_detail: str | None
    severity: str
    confidence_score: float | None
    affected_resources: list[dict[str, Any]] | None
    supporting_evidence: list[dict[str, Any]] | None
    remediation_recommendations: list[dict[str, Any]] | None
    investigation_context: dict[str, Any] | None
    context_sources: list[str] | None
    llm_provider: str | None
    llm_model: str | None
    tokens_used: int | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InvestigationListResponse(BaseModel):
    items: list[InvestigationOut]
    total: int
    page: int
    page_size: int


class InvestigationEvidenceOut(BaseModel):
    id: str
    investigation_id: str
    evidence_type: str
    severity: str
    title: str
    description: str
    resource_type: str | None
    resource_name: str | None
    cluster_id: str | None
    namespace_name: str | None
    deployment_name: str | None
    pod_name: str | None
    service_name: str | None
    source_id: str | None
    source_type: str | None
    observed_at: datetime | None
    metadata_: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvestigationRunResponse(BaseModel):
    investigation: InvestigationOut
    evidence: list[InvestigationEvidenceOut]
