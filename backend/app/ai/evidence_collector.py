"""Evidence collection and signal extraction for incident investigations."""

from statistics import mean
from typing import Any

from app.models.incident import Incident
from app.models.investigation import InvestigationEvidence
from app.repositories.telemetry_repository import TelemetryRepository

SEVERITY_RANK = {"info": 1, "low": 2, "medium": 3, "warning": 3, "high": 4, "critical": 5, "error": 5}


class EvidenceCollector:
    """Collects and normalizes metrics, logs, events, and traces for an incident."""

    def __init__(self, telemetry_repo: TelemetryRepository):
        self.telemetry_repo = telemetry_repo

    async def collect(self, incident: Incident | None, cluster_id: str | None, limit: int = 250) -> list[InvestigationEvidence]:
        cluster_id = cluster_id or (incident.cluster_id if incident else None)
        namespace = incident.namespace if incident else None
        workload = incident.affected_workload if incident else None

        metrics = await self.telemetry_repo.list_metrics(
            cluster_id=cluster_id,
            namespace_name=namespace,
            deployment_name=workload,
            limit=limit,
        )
        logs = await self.telemetry_repo.list_logs(
            cluster_id=cluster_id,
            namespace_name=namespace,
            deployment_name=workload,
            limit=80,
        )
        events = await self.telemetry_repo.list_events(
            cluster_id=cluster_id,
            namespace_name=namespace,
            deployment_name=workload,
            limit=80,
        )
        traces = await self.telemetry_repo.list_traces(
            cluster_id=cluster_id,
            namespace_name=namespace,
            deployment_name=workload,
            limit=80,
        )

        evidence: list[InvestigationEvidence] = []
        evidence.extend(self._metric_evidence(metrics))
        evidence.extend(self._log_evidence(logs))
        evidence.extend(self._event_evidence(events))
        evidence.extend(self._trace_evidence(traces))
        if not evidence and (namespace or workload):
            metrics = await self.telemetry_repo.list_metrics(cluster_id=cluster_id, limit=limit)
            logs = await self.telemetry_repo.list_logs(cluster_id=cluster_id, limit=80)
            events = await self.telemetry_repo.list_events(cluster_id=cluster_id, limit=80)
            traces = await self.telemetry_repo.list_traces(cluster_id=cluster_id, limit=80)
            evidence.extend(self._metric_evidence(metrics))
            evidence.extend(self._log_evidence(logs))
            evidence.extend(self._event_evidence(events))
            evidence.extend(self._trace_evidence(traces))
        evidence.sort(key=lambda item: SEVERITY_RANK.get(item.severity, 1), reverse=True)
        return evidence

    def _metric_evidence(self, metrics) -> list[InvestigationEvidence]:
        by_name: dict[str, list[Any]] = {}
        for metric in metrics:
            by_name.setdefault(metric.metric_name, []).append(metric)

        evidence = []
        for name, rows in by_name.items():
            values = [row.value for row in rows[:24]]
            if not values:
                continue
            latest = rows[0]
            avg = mean(values)
            peak = max(values)
            severity = "info"
            title = None
            if name == "cpu_usage_percent" and peak >= 85:
                severity = "high" if peak >= 93 else "medium"
                title = f"CPU pressure peaked at {peak:.1f}%"
            elif name == "memory_usage_percent" and peak >= 85:
                severity = "critical" if peak >= 94 else "high"
                title = f"Memory pressure peaked at {peak:.1f}%"
            elif name == "error_rate_percent" and peak >= 2:
                severity = "critical" if peak >= 5 else "high"
                title = f"Error rate elevated to {peak:.2f}%"
            elif name == "pod_restarts" and peak >= 2:
                severity = "high" if peak >= 5 else "medium"
                title = f"Pod restart trend reached {peak:.0f}"

            if title:
                evidence.append(
                    InvestigationEvidence(
                        evidence_type="metric",
                        severity=severity,
                        title=title,
                        description=f"{name} averaged {avg:.2f} with peak {peak:.2f} across recent samples.",
                        resource_type=latest.resource_type,
                        resource_name=latest.resource_name,
                        cluster_id=latest.cluster_id,
                        namespace_name=latest.namespace_name,
                        deployment_name=latest.deployment_name,
                        pod_name=latest.pod_name,
                        service_name=latest.service_name,
                        source_id=latest.id,
                        source_type="metric",
                        observed_at=latest.timestamp,
                        metadata_={"metric_name": name, "average": avg, "peak": peak, "unit": latest.unit},
                    )
                )
        return evidence

    def _log_evidence(self, logs) -> list[InvestigationEvidence]:
        evidence = []
        for log in logs:
            if log.severity not in {"error", "critical", "warn", "warning"}:
                continue
            severity = "critical" if log.severity in {"error", "critical"} else "medium"
            evidence.append(
                InvestigationEvidence(
                    evidence_type="log",
                    severity=severity,
                    title=f"{log.severity.upper()} log from {log.pod_name or log.deployment_name or log.source}",
                    description=log.message[:1000],
                    resource_type="pod" if log.pod_name else "deployment" if log.deployment_name else "service",
                    resource_name=log.pod_name or log.deployment_name or log.service_name or log.source,
                    cluster_id=log.cluster_id,
                    namespace_name=log.namespace_name,
                    deployment_name=log.deployment_name,
                    pod_name=log.pod_name,
                    service_name=log.service_name,
                    source_id=log.id,
                    source_type="log",
                    observed_at=log.timestamp,
                    metadata_={"trace_id": log.trace_id, "attributes": log.attributes or {}},
                )
            )
        return evidence[:20]

    def _event_evidence(self, events) -> list[InvestigationEvidence]:
        evidence = []
        for event in events:
            if event.severity in {"normal", "info"} and event.reason not in {"PodRestarted", "ReplicaSetDegraded"}:
                continue
            evidence.append(
                InvestigationEvidence(
                    evidence_type="event",
                    severity="critical" if event.severity == "critical" else "high" if event.severity == "warning" else event.severity,
                    title=f"{event.reason} on {event.resource_name}",
                    description=event.message,
                    resource_type=event.resource_type,
                    resource_name=event.resource_name,
                    cluster_id=event.cluster_id,
                    namespace_name=event.namespace_name,
                    deployment_name=event.deployment_name,
                    pod_name=event.pod_name,
                    service_name=event.service_name,
                    source_id=event.id,
                    source_type="event",
                    observed_at=event.timestamp,
                    metadata_=event.attributes or {},
                )
            )
        return evidence[:20]

    def _trace_evidence(self, traces) -> list[InvestigationEvidence]:
        evidence = []
        for trace in traces:
            if trace.status == "ok" and trace.duration_ms < 400:
                continue
            evidence.append(
                InvestigationEvidence(
                    evidence_type="trace",
                    severity="critical" if trace.status != "ok" else "medium",
                    title=f"Trace span {trace.operation_name} took {trace.duration_ms}ms",
                    description=f"{trace.service_name} span status={trace.status}, duration={trace.duration_ms}ms.",
                    resource_type="deployment",
                    resource_name=trace.deployment_name or trace.service_name,
                    cluster_id=trace.cluster_id,
                    namespace_name=trace.namespace_name,
                    deployment_name=trace.deployment_name,
                    pod_name=trace.pod_name,
                    source_id=trace.id,
                    source_type="trace",
                    observed_at=trace.start_time,
                    metadata_={"trace_id": trace.trace_id, "span_id": trace.span_id, "attributes": trace.attributes or {}},
                )
            )
        return evidence[:20]
