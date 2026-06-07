"""Repository for telemetry persistence and retrieval."""

from collections.abc import Sequence

from sqlalchemy import delete, func, select

from app.models.telemetry import InfrastructureEvent, LogEntry, Metric, TelemetrySource, Trace
from app.repositories.base import BaseRepository


class TelemetryRepository(BaseRepository[TelemetrySource]):
    """Data access helpers for metrics, logs, events, traces, and sources."""

    async def get_source_by_name(self, name: str) -> TelemetrySource | None:
        result = await self.session.execute(select(TelemetrySource).where(TelemetrySource.name == name))
        return result.scalar_one_or_none()

    async def get_or_create_source(
        self,
        name: str,
        source_type: str,
        endpoint_url: str | None = None,
        cluster_id: str | None = None,
        config: dict | None = None,
    ) -> TelemetrySource:
        source = await self.get_source_by_name(name)
        if not source:
            source = TelemetrySource(
                name=name,
                source_type=source_type,
                endpoint_url=endpoint_url,
                cluster_id=cluster_id,
                config=config or {},
                is_active=True,
            )
            self.session.add(source)
            await self.session.flush()
        else:
            source.source_type = source_type
            source.endpoint_url = endpoint_url
            source.cluster_id = cluster_id
            source.config = config or source.config or {}
            source.is_active = True
            await self.session.flush()
        return source

    async def replace_source_telemetry(
        self,
        source_id: str,
        metrics: list[Metric],
        logs: list[LogEntry],
        events: list[InfrastructureEvent],
        traces: list[Trace],
    ) -> dict[str, int]:
        """Replace generated telemetry for a source while preserving its source identity."""
        for model in (Trace, InfrastructureEvent, LogEntry, Metric):
            await self.session.execute(delete(model).where(model.source_id == source_id))

        self.session.add_all(metrics)
        self.session.add_all(logs)
        self.session.add_all(events)
        self.session.add_all(traces)
        await self.session.flush()

        return {
            "metrics": len(metrics),
            "logs": len(logs),
            "events": len(events),
            "traces": len(traces),
        }

    async def list_sources(self, active_only: bool = True) -> Sequence[TelemetrySource]:
        stmt = select(TelemetrySource).order_by(TelemetrySource.name)
        if active_only:
            stmt = stmt.where(TelemetrySource.is_active.is_(True))
        result = await self.session.execute(stmt)
        return result.scalars().all()

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
        stmt = select(Metric)
        stmt = self._apply_resource_filters(
            stmt,
            Metric,
            cluster_id=cluster_id,
            namespace_name=namespace_name,
            deployment_name=deployment_name,
            pod_name=pod_name,
            service_name=service_name,
            incident_id=incident_id,
        )
        if metric_name:
            stmt = stmt.where(Metric.metric_name == metric_name)
        stmt = stmt.order_by(Metric.timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

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
        stmt = select(LogEntry)
        stmt = self._apply_resource_filters(
            stmt,
            LogEntry,
            cluster_id=cluster_id,
            namespace_name=namespace_name,
            deployment_name=deployment_name,
            pod_name=pod_name,
            service_name=service_name,
            incident_id=incident_id,
        )
        if severity:
            stmt = stmt.where(LogEntry.severity == severity)
        stmt = stmt.order_by(LogEntry.timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

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
        stmt = select(InfrastructureEvent)
        stmt = self._apply_resource_filters(
            stmt,
            InfrastructureEvent,
            cluster_id=cluster_id,
            namespace_name=namespace_name,
            deployment_name=deployment_name,
            pod_name=pod_name,
            service_name=service_name,
            incident_id=incident_id,
        )
        if severity:
            stmt = stmt.where(InfrastructureEvent.severity == severity)
        if resource_type:
            stmt = stmt.where(InfrastructureEvent.resource_type == resource_type)
        stmt = stmt.order_by(InfrastructureEvent.timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

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
        stmt = select(Trace)
        stmt = self._apply_resource_filters(
            stmt,
            Trace,
            cluster_id=cluster_id,
            namespace_name=namespace_name,
            deployment_name=deployment_name,
            pod_name=pod_name,
            service_name=None,
            incident_id=incident_id,
        )
        stmt = stmt.order_by(Trace.start_time.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def summary(self, cluster_id: str | None = None) -> dict:
        filters = []
        if cluster_id:
            filters.append(lambda model: model.cluster_id == cluster_id)

        async def count(model) -> int:
            stmt = select(func.count()).select_from(model)
            for apply_filter in filters:
                stmt = stmt.where(apply_filter(model))
            result = await self.session.execute(stmt)
            return result.scalar_one()

        latest_metric = await self.session.execute(select(func.max(Metric.timestamp)))
        latest_log = await self.session.execute(select(func.max(LogEntry.timestamp)))
        latest_event = await self.session.execute(select(func.max(InfrastructureEvent.timestamp)))
        latest_trace = await self.session.execute(select(func.max(Trace.start_time)))
        timestamps = [
            latest_metric.scalar_one_or_none(),
            latest_log.scalar_one_or_none(),
            latest_event.scalar_one_or_none(),
            latest_trace.scalar_one_or_none(),
        ]
        return {
            "metrics": await count(Metric),
            "logs": await count(LogEntry),
            "events": await count(InfrastructureEvent),
            "traces": await count(Trace),
            "sources": await count(TelemetrySource),
            "latest_timestamp": max([ts for ts in timestamps if ts], default=None),
        }

    def _apply_resource_filters(
        self,
        stmt,
        model,
        *,
        cluster_id: str | None,
        namespace_name: str | None,
        deployment_name: str | None,
        pod_name: str | None,
        service_name: str | None,
        incident_id: str | None,
    ):
        if cluster_id:
            stmt = stmt.where(model.cluster_id == cluster_id)
        if namespace_name:
            stmt = stmt.where(model.namespace_name == namespace_name)
        if deployment_name and hasattr(model, "deployment_name"):
            stmt = stmt.where(model.deployment_name == deployment_name)
        if pod_name and hasattr(model, "pod_name"):
            stmt = stmt.where(model.pod_name == pod_name)
        if service_name and hasattr(model, "service_name"):
            stmt = stmt.where(model.service_name == service_name)
        if incident_id:
            stmt = stmt.where(model.incident_id == incident_id)
        return stmt
