"""Typed API schemas for observability telemetry."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TelemetrySourceOut(BaseModel):
    id: str
    name: str
    source_type: str
    endpoint_url: str | None
    cluster_id: str | None
    is_active: bool
    config: dict | None
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
    resource_name: str | None
    source_id: str | None
    cluster_id: str | None
    namespace_name: str | None
    deployment_name: str | None
    pod_name: str | None
    service_name: str | None
    incident_id: str | None
    labels: dict | None

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
    source_id: str | None
    cluster_id: str | None
    namespace_name: str | None
    deployment_name: str | None
    pod_name: str | None
    service_name: str | None
    incident_id: str | None
    trace_id: str | None
    span_id: str | None
    attributes: dict | None

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
    source_id: str | None
    cluster_id: str | None
    namespace_name: str | None
    deployment_name: str | None
    pod_name: str | None
    service_name: str | None
    incident_id: str | None
    attributes: dict | None

    model_config = {"from_attributes": True}


class TraceOut(BaseModel):
    id: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    operation_name: str
    service_name: str
    status: str
    start_time: datetime
    end_time: datetime
    duration_ms: int
    source_id: str | None
    cluster_id: str | None
    namespace_name: str | None
    deployment_name: str | None
    pod_name: str | None
    incident_id: str | None
    attributes: dict | None

    model_config = {"from_attributes": True}


class TelemetrySummaryOut(BaseModel):
    metrics: int
    logs: int
    events: int
    traces: int
    sources: int
    latest_timestamp: datetime | None = None


class DemoTelemetryResponse(BaseModel):
    status: str = "generated"
    clusters: int
    metrics: int
    logs: int
    events: int
    traces: int
    source: TelemetrySourceOut


class TelemetryQuery(BaseModel):
    cluster_id: str | None = None
    namespace_name: str | None = None
    deployment_name: str | None = None
    pod_name: str | None = None
    service_name: str | None = None
    incident_id: str | None = None
    limit: int = Field(default=200, ge=1, le=1000)
    metric_name: str | None = None
    severity: str | None = None
    resource_type: str | None = None
    labels: dict[str, Any] | None = None
