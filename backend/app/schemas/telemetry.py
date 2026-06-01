"""Typed API schemas for observability telemetry."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TelemetrySourceOut(BaseModel):
    id: str
    name: str
    source_type: str
    endpoint_url: Optional[str]
    cluster_id: Optional[str]
    is_active: bool
    config: Optional[dict]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MetricOut(BaseModel):
    id: str
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    resource_type: str
    resource_name: Optional[str]
    source_id: Optional[str]
    cluster_id: Optional[str]
    namespace_name: Optional[str]
    deployment_name: Optional[str]
    pod_name: Optional[str]
    service_name: Optional[str]
    incident_id: Optional[str]
    labels: Optional[dict]

    model_config = {"from_attributes": True}


class MetricSeriesOut(BaseModel):
    metric_name: str
    unit: str
    points: list[MetricOut]


class LogEntryOut(BaseModel):
    id: str
    timestamp: datetime
    severity: str
    source: str
    message: str
    source_id: Optional[str]
    cluster_id: Optional[str]
    namespace_name: Optional[str]
    deployment_name: Optional[str]
    pod_name: Optional[str]
    service_name: Optional[str]
    incident_id: Optional[str]
    trace_id: Optional[str]
    span_id: Optional[str]
    attributes: Optional[dict]

    model_config = {"from_attributes": True}


class InfrastructureEventOut(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    reason: str
    severity: str
    message: str
    resource_type: str
    resource_name: str
    source_id: Optional[str]
    cluster_id: Optional[str]
    namespace_name: Optional[str]
    deployment_name: Optional[str]
    pod_name: Optional[str]
    service_name: Optional[str]
    incident_id: Optional[str]
    attributes: Optional[dict]

    model_config = {"from_attributes": True}


class TraceOut(BaseModel):
    id: str
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration_ms: int
    source_id: Optional[str]
    cluster_id: Optional[str]
    namespace_name: Optional[str]
    deployment_name: Optional[str]
    pod_name: Optional[str]
    incident_id: Optional[str]
    attributes: Optional[dict]

    model_config = {"from_attributes": True}


class TelemetrySummaryOut(BaseModel):
    metrics: int
    logs: int
    events: int
    traces: int
    sources: int
    latest_timestamp: Optional[datetime] = None


class DemoTelemetryResponse(BaseModel):
    status: str = "generated"
    clusters: int
    metrics: int
    logs: int
    events: int
    traces: int
    source: TelemetrySourceOut


class TelemetryQuery(BaseModel):
    cluster_id: Optional[str] = None
    namespace_name: Optional[str] = None
    deployment_name: Optional[str] = None
    pod_name: Optional[str] = None
    service_name: Optional[str] = None
    incident_id: Optional[str] = None
    limit: int = Field(default=200, ge=1, le=1000)
    metric_name: Optional[str] = None
    severity: Optional[str] = None
    resource_type: Optional[str] = None
    labels: Optional[dict[str, Any]] = None
