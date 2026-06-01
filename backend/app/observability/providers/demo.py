"""Demo telemetry provider using the same persistence model as real telemetry."""

from datetime import datetime, timedelta, timezone
from hashlib import sha1
from random import Random
from typing import Sequence
from uuid import uuid4

from app.models.cluster import Cluster, KubernetesPod, KubernetesWorkload
from app.observability.providers.base import TelemetrySnapshot


class DemoTelemetryProvider:
    """Generate enterprise-like metrics, logs, events, and traces for demos."""

    source_type = "demo"

    def collect(self, clusters: Sequence[Cluster], source_id: str) -> TelemetrySnapshot:
        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        snapshot = TelemetrySnapshot()

        for cluster in clusters:
            rng = Random(self._seed(cluster.name))
            unhealthy = any(not workload.is_healthy for workload in cluster.workloads)
            pod_restarts = sum(pod.restart_count for pod in cluster.pods)
            cluster_factor = 1.25 if unhealthy or cluster.status in {"degraded", "critical"} else 1.0

            for index in range(24):
                timestamp = now - timedelta(hours=23 - index)
                wave = 0.5 + (index % 8) / 10
                cpu = min(98, self._average(cluster.workloads, "cpu_usage_percent", 41) * cluster_factor + rng.uniform(-4, 6) + wave)
                memory = min(96, self._average(cluster.workloads, "memory_usage_percent", 47) * cluster_factor + rng.uniform(-3, 5))
                error_rate = max(0.02, (2.2 if unhealthy else 0.35) + rng.uniform(-0.12, 0.35))
                requests = int((4500 if cluster.environment == "production" else 1100) * cluster_factor + rng.randint(-260, 360))
                restarts = max(0, int(pod_restarts / max(1, len(cluster.pods)) + rng.choice([0, 0, 1, 2 if unhealthy else 0])))

                snapshot.metrics.extend(
                    [
                        self._metric(source_id, cluster, timestamp, "cpu_usage_percent", round(cpu, 2), "%"),
                        self._metric(source_id, cluster, timestamp, "memory_usage_percent", round(memory, 2), "%"),
                        self._metric(source_id, cluster, timestamp, "network_rx_mbps", round(rng.uniform(80, 420) * cluster_factor, 2), "mbps"),
                        self._metric(source_id, cluster, timestamp, "network_tx_mbps", round(rng.uniform(45, 260) * cluster_factor, 2), "mbps"),
                        self._metric(source_id, cluster, timestamp, "request_count", requests, "requests"),
                        self._metric(source_id, cluster, timestamp, "error_rate_percent", round(error_rate, 2), "%"),
                        self._metric(source_id, cluster, timestamp, "pod_restarts", restarts, "restarts"),
                    ]
                )

                for workload in list(cluster.workloads)[:4]:
                    workload_cpu = min(99, (workload.cpu_usage_percent or cpu) + rng.uniform(-5, 8))
                    workload_memory = min(98, (workload.memory_usage_percent or memory) + rng.uniform(-4, 7))
                    workload_error = max(0.01, error_rate + (1.5 if not workload.is_healthy else 0) + rng.uniform(-0.15, 0.2))
                    snapshot.metrics.extend(
                        [
                            self._metric(
                                source_id,
                                cluster,
                                timestamp,
                                "cpu_usage_percent",
                                round(workload_cpu, 2),
                                "%",
                                workload=workload,
                            ),
                            self._metric(
                                source_id,
                                cluster,
                                timestamp,
                                "memory_usage_percent",
                                round(workload_memory, 2),
                                "%",
                                workload=workload,
                            ),
                            self._metric(
                                source_id,
                                cluster,
                                timestamp,
                                "error_rate_percent",
                                round(workload_error, 2),
                                "%",
                                workload=workload,
                            ),
                        ]
                    )

            snapshot.logs.extend(self._logs(cluster, source_id, now, rng))
            snapshot.events.extend(self._events(cluster, source_id, now, rng))
            snapshot.traces.extend(self._traces(cluster, source_id, now, rng))

        return snapshot

    def _metric(
        self,
        source_id: str,
        cluster: Cluster,
        timestamp: datetime,
        metric_name: str,
        value: float,
        unit: str,
        workload: KubernetesWorkload | None = None,
        pod: KubernetesPod | None = None,
    ) -> dict:
        return {
            "source_id": source_id,
            "cluster_id": cluster.id,
            "timestamp": timestamp,
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "resource_type": "deployment" if workload else "pod" if pod else "cluster",
            "resource_name": (workload.name if workload else pod.name if pod else cluster.name),
            "namespace_name": (workload.namespace_name if workload else pod.namespace_name if pod else None),
            "deployment_name": workload.name if workload else None,
            "pod_name": pod.name if pod else None,
            "labels": {"provider": "demo", "environment": cluster.environment},
        }

    def _logs(self, cluster: Cluster, source_id: str, now: datetime, rng: Random) -> list[dict]:
        logs = []
        pods = list(cluster.pods)[:10]
        for index, pod in enumerate(pods):
            workload = self._workload_for_pod(cluster, pod)
            severity = "error" if pod.restart_count > 3 or pod.status in {"CrashLoopBackOff", "Error"} else rng.choice(["info", "info", "warn"])
            message = (
                f"Container restart detected in {pod.name}; back-off restarting failed container"
                if severity == "error"
                else f"{pod.name} processed request batch with p95 latency {rng.randint(85, 420)}ms"
            )
            logs.append(
                {
                    "source_id": source_id,
                    "cluster_id": cluster.id,
                    "timestamp": now - timedelta(minutes=7 * index + rng.randint(0, 12)),
                    "severity": severity,
                    "source": "demo-loki",
                    "message": message,
                    "namespace_name": pod.namespace_name,
                    "deployment_name": workload.name if workload else None,
                    "pod_name": pod.name,
                    "attributes": {"node": pod.node_name, "provider": "demo"},
                }
            )
        return logs

    def _events(self, cluster: Cluster, source_id: str, now: datetime, rng: Random) -> list[dict]:
        events = []
        for index, workload in enumerate(list(cluster.workloads)[:8]):
            severity = "warning" if not workload.is_healthy else rng.choice(["info", "normal"])
            reason = "ReplicaSetDegraded" if not workload.is_healthy else rng.choice(["DeploymentUpdated", "ScalingReplicaSet"])
            events.append(
                {
                    "source_id": source_id,
                    "cluster_id": cluster.id,
                    "timestamp": now - timedelta(minutes=11 * index + rng.randint(1, 20)),
                    "event_type": "kubernetes.deployment",
                    "reason": reason,
                    "severity": severity,
                    "message": (
                        f"{workload.name} has {workload.replicas_ready}/{workload.replicas_desired} replicas ready"
                        if not workload.is_healthy
                        else f"{workload.name} successfully rolled out in namespace {workload.namespace_name}"
                    ),
                    "resource_type": "deployment",
                    "resource_name": workload.name,
                    "namespace_name": workload.namespace_name,
                    "deployment_name": workload.name,
                    "attributes": {"replicas_ready": workload.replicas_ready, "replicas_desired": workload.replicas_desired},
                }
            )

        for index, pod in enumerate([pod for pod in cluster.pods if pod.restart_count > 0][:4]):
            events.append(
                {
                    "source_id": source_id,
                    "cluster_id": cluster.id,
                    "timestamp": now - timedelta(minutes=5 * index + 3),
                    "event_type": "kubernetes.pod",
                    "reason": "PodRestarted",
                    "severity": "warning" if pod.restart_count < 5 else "critical",
                    "message": f"{pod.name} restarted {pod.restart_count} times",
                    "resource_type": "pod",
                    "resource_name": pod.name,
                    "namespace_name": pod.namespace_name,
                    "pod_name": pod.name,
                    "attributes": {"restart_count": pod.restart_count, "phase": pod.phase},
                }
            )
        return events

    def _traces(self, cluster: Cluster, source_id: str, now: datetime, rng: Random) -> list[dict]:
        traces = []
        workloads = list(cluster.workloads)[:5] or []
        for index, workload in enumerate(workloads):
            trace_id = uuid4().hex
            started = now - timedelta(minutes=4 * index + rng.randint(1, 8))
            services = [
                ("frontend", "GET /dashboard", None, 38),
                ("api-gateway", "GET /api/v1/clusters", "frontend", 82),
                ("auth-service", "validate token", "api-gateway", 26),
                (workload.name, "query workload telemetry", "api-gateway", 140 if workload.is_healthy else 520),
                ("postgres", "SELECT telemetry window", workload.name, 45),
            ]
            span_ids: dict[str, str] = {}
            for service_name, operation, parent_service, base_duration in services:
                span_id = uuid4().hex[:16]
                span_ids[service_name] = span_id
                duration = max(5, base_duration + rng.randint(-12, 45))
                status = "error" if (not workload.is_healthy and service_name == workload.name) else "ok"
                traces.append(
                    {
                        "source_id": source_id,
                        "cluster_id": cluster.id,
                        "trace_id": trace_id,
                        "span_id": span_id,
                        "parent_span_id": span_ids.get(parent_service or ""),
                        "operation_name": operation,
                        "service_name": service_name,
                        "status": status,
                        "start_time": started,
                        "end_time": started + timedelta(milliseconds=duration),
                        "duration_ms": duration,
                        "namespace_name": workload.namespace_name,
                        "deployment_name": workload.name,
                        "attributes": {"provider": "demo", "cluster": cluster.name},
                    }
                )
                started += timedelta(milliseconds=rng.randint(3, 18))
        return traces

    def _workload_for_pod(self, cluster: Cluster, pod: KubernetesPod) -> KubernetesWorkload | None:
        return next((workload for workload in cluster.workloads if workload.id == pod.workload_id), None)

    def _average(self, rows, attr: str, default: float) -> float:
        values = [getattr(row, attr) for row in rows if getattr(row, attr) is not None]
        return sum(values) / len(values) if values else default

    def _seed(self, value: str) -> int:
        return int(sha1(value.encode("utf-8")).hexdigest()[:8], 16)
