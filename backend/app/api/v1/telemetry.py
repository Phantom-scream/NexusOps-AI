"""Observability telemetry API."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.models.cluster import Cluster
from app.models.telemetry import TelemetrySource
from app.repositories.cluster_repository import ClusterRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.telemetry import (
    DemoTelemetryResponse,
    InfrastructureEventOut,
    LogEntryOut,
    MetricOut,
    TelemetrySourceOut,
    TelemetrySummaryOut,
    TraceOut,
)
from app.services.telemetry_service import TelemetryService

router = APIRouter()


def get_telemetry_service(db: AsyncSession = Depends(get_db)) -> TelemetryService:
    return TelemetryService(
        telemetry_repo=TelemetryRepository(model=TelemetrySource, session=db),
        cluster_repo=ClusterRepository(model=Cluster, session=db),
    )


@router.get("/telemetry/sources", response_model=list[TelemetrySourceOut])
async def list_telemetry_sources(
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List telemetry providers currently known to the platform."""
    return [TelemetrySourceOut.model_validate(source) for source in await service.list_sources()]


@router.get("/telemetry/summary", response_model=TelemetrySummaryOut)
async def get_telemetry_summary(
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get aggregate telemetry counts for dashboards and health checks."""
    return TelemetrySummaryOut.model_validate(await service.summary())


@router.get("/metrics", response_model=list[MetricOut])
async def list_metrics(
    metric_name: Optional[str] = Query(default=None),
    cluster_id: Optional[str] = Query(default=None),
    namespace_name: Optional[str] = Query(default=None),
    deployment_name: Optional[str] = Query(default=None),
    pod_name: Optional[str] = Query(default=None),
    service_name: Optional[str] = Query(default=None),
    incident_id: Optional[str] = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List historical metrics with optional resource filters."""
    metrics = await service.list_metrics(
        cluster_id=cluster_id,
        metric_name=metric_name,
        namespace_name=namespace_name,
        deployment_name=deployment_name,
        pod_name=pod_name,
        service_name=service_name,
        incident_id=incident_id,
        limit=limit,
    )
    return [MetricOut.model_validate(metric) for metric in metrics]


@router.get("/logs", response_model=list[LogEntryOut])
async def list_logs(
    cluster_id: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    namespace_name: Optional[str] = Query(default=None),
    deployment_name: Optional[str] = Query(default=None),
    pod_name: Optional[str] = Query(default=None),
    service_name: Optional[str] = Query(default=None),
    incident_id: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List centralized logs with optional resource filters."""
    logs = await service.list_logs(
        cluster_id=cluster_id,
        severity=severity,
        namespace_name=namespace_name,
        deployment_name=deployment_name,
        pod_name=pod_name,
        service_name=service_name,
        incident_id=incident_id,
        limit=limit,
    )
    return [LogEntryOut.model_validate(log) for log in logs]


@router.get("/events", response_model=list[InfrastructureEventOut])
async def list_events(
    cluster_id: Optional[str] = Query(default=None),
    severity: Optional[str] = Query(default=None),
    resource_type: Optional[str] = Query(default=None),
    namespace_name: Optional[str] = Query(default=None),
    deployment_name: Optional[str] = Query(default=None),
    pod_name: Optional[str] = Query(default=None),
    service_name: Optional[str] = Query(default=None),
    incident_id: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List normalized infrastructure events."""
    events = await service.list_events(
        cluster_id=cluster_id,
        severity=severity,
        resource_type=resource_type,
        namespace_name=namespace_name,
        deployment_name=deployment_name,
        pod_name=pod_name,
        service_name=service_name,
        incident_id=incident_id,
        limit=limit,
    )
    return [InfrastructureEventOut.model_validate(event) for event in events]


@router.get("/traces", response_model=list[TraceOut])
async def list_traces(
    cluster_id: Optional[str] = Query(default=None),
    namespace_name: Optional[str] = Query(default=None),
    deployment_name: Optional[str] = Query(default=None),
    pod_name: Optional[str] = Query(default=None),
    incident_id: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List persisted trace spans."""
    traces = await service.list_traces(
        cluster_id=cluster_id,
        namespace_name=namespace_name,
        deployment_name=deployment_name,
        pod_name=pod_name,
        incident_id=incident_id,
        limit=limit,
    )
    return [TraceOut.model_validate(trace) for trace in traces]


@router.get("/clusters/{cluster_id}/metrics", response_model=list[MetricOut])
async def list_cluster_metrics(
    cluster_id: str,
    metric_name: Optional[str] = Query(default=None),
    limit: int = Query(default=500, ge=1, le=2000),
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List metrics for one cluster."""
    metrics = await service.list_metrics(cluster_id=cluster_id, metric_name=metric_name, limit=limit)
    return [MetricOut.model_validate(metric) for metric in metrics]


@router.get("/clusters/{cluster_id}/logs", response_model=list[LogEntryOut])
async def list_cluster_logs(
    cluster_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List logs for one cluster."""
    logs = await service.list_logs(cluster_id=cluster_id, limit=limit)
    return [LogEntryOut.model_validate(log) for log in logs]


@router.get("/clusters/{cluster_id}/events", response_model=list[InfrastructureEventOut])
async def list_cluster_events(
    cluster_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List events for one cluster."""
    events = await service.list_events(cluster_id=cluster_id, limit=limit)
    return [InfrastructureEventOut.model_validate(event) for event in events]


@router.get("/clusters/{cluster_id}/traces", response_model=list[TraceOut])
async def list_cluster_traces(
    cluster_id: str,
    limit: int = Query(default=200, ge=1, le=1000),
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List trace spans for one cluster."""
    traces = await service.list_traces(cluster_id=cluster_id, limit=limit)
    return [TraceOut.model_validate(trace) for trace in traces]


@router.post("/demo/telemetry/generate", response_model=DemoTelemetryResponse)
async def generate_demo_telemetry(
    service: TelemetryService = Depends(get_telemetry_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Generate demo telemetry from persisted demo or Kubernetes topology."""
    source, counts = await service.generate_demo_telemetry()
    return DemoTelemetryResponse(
        source=TelemetrySourceOut.model_validate(source),
        clusters=counts["clusters"],
        metrics=counts["metrics"],
        logs=counts["logs"],
        events=counts["events"],
        traces=counts["traces"],
    )
