"""Telemetry ingestion and query orchestration."""

from collections.abc import Sequence

import structlog

from app.models.cluster import Cluster
from app.models.telemetry import InfrastructureEvent, LogEntry, Metric, TelemetrySource, Trace
from app.observability.providers import DemoTelemetryProvider, TelemetryProvider
from app.repositories.cluster_repository import ClusterRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.services.infrastructure_discovery_service import InfrastructureDiscoveryService

logger = structlog.get_logger(__name__)


class TelemetryService:
    """Coordinates telemetry providers and persistence."""

    def __init__(self, telemetry_repo: TelemetryRepository, cluster_repo: ClusterRepository):
        self.telemetry_repo = telemetry_repo
        self.cluster_repo = cluster_repo

    async def generate_demo_telemetry(self) -> tuple[TelemetrySource, dict[str, int]]:
        clusters = list(await self.cluster_repo.get_active_clusters_with_topology())
        if not clusters:
            discovery = InfrastructureDiscoveryService(repository=self.cluster_repo)
            await discovery.generate_demo_environment()
            clusters = list(await self.cluster_repo.get_active_clusters_with_topology())

        source = await self.telemetry_repo.get_or_create_source(
            name="demo-telemetry",
            source_type="demo",
            config={"mode": "deterministic-demo", "cluster_count": len(clusters)},
        )
        counts = await self.ingest_from_provider(DemoTelemetryProvider(), clusters, source)
        logger.info("Demo telemetry generated", clusters=len(clusters), **counts)
        return source, {"clusters": len(clusters), **counts}

    async def ingest_from_provider(
        self,
        provider: TelemetryProvider,
        clusters: Sequence[Cluster],
        source: TelemetrySource,
    ) -> dict[str, int]:
        snapshot = provider.collect(clusters, source.id)
        metrics = [Metric(**payload) for payload in snapshot.metrics]
        logs = [LogEntry(**payload) for payload in snapshot.logs]
        events = [InfrastructureEvent(**payload) for payload in snapshot.events]
        traces = [Trace(**payload) for payload in snapshot.traces]
        return await self.telemetry_repo.replace_source_telemetry(
            source_id=source.id,
            metrics=metrics,
            logs=logs,
            events=events,
            traces=traces,
        )

    async def list_sources(self) -> Sequence[TelemetrySource]:
        return await self.telemetry_repo.list_sources()

    async def list_metrics(
        self,
        *,
        cluster_id: str | None = None,
        metric_name: str | None = None,
        namespace_name: str | None = None,
        deployment_name: str | None = None,
        pod_name: str | None = None,
        service_name: str | None = None,
        incident_id: str | None = None,
        limit: int = 500,
    ) -> Sequence[Metric]:
        return await self.telemetry_repo.list_metrics(
            cluster_id=cluster_id,
            metric_name=metric_name,
            namespace_name=namespace_name,
            deployment_name=deployment_name,
            pod_name=pod_name,
            service_name=service_name,
            incident_id=incident_id,
            limit=limit,
        )

    async def list_logs(
        self,
        *,
        cluster_id: str | None = None,
        severity: str | None = None,
        namespace_name: str | None = None,
        deployment_name: str | None = None,
        pod_name: str | None = None,
        service_name: str | None = None,
        incident_id: str | None = None,
        limit: int = 200,
    ) -> Sequence[LogEntry]:
        return await self.telemetry_repo.list_logs(
            cluster_id=cluster_id,
            severity=severity,
            namespace_name=namespace_name,
            deployment_name=deployment_name,
            pod_name=pod_name,
            service_name=service_name,
            incident_id=incident_id,
            limit=limit,
        )

    async def list_events(
        self,
        *,
        cluster_id: str | None = None,
        severity: str | None = None,
        resource_type: str | None = None,
        namespace_name: str | None = None,
        deployment_name: str | None = None,
        pod_name: str | None = None,
        service_name: str | None = None,
        incident_id: str | None = None,
        limit: int = 200,
    ) -> Sequence[InfrastructureEvent]:
        return await self.telemetry_repo.list_events(
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

    async def list_traces(
        self,
        *,
        cluster_id: str | None = None,
        namespace_name: str | None = None,
        deployment_name: str | None = None,
        pod_name: str | None = None,
        incident_id: str | None = None,
        limit: int = 200,
    ) -> Sequence[Trace]:
        return await self.telemetry_repo.list_traces(
            cluster_id=cluster_id,
            namespace_name=namespace_name,
            deployment_name=deployment_name,
            pod_name=pod_name,
            incident_id=incident_id,
            limit=limit,
        )

    async def summary(self, cluster_id: str | None = None) -> dict:
        return await self.telemetry_repo.summary(cluster_id=cluster_id)
