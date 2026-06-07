"""Demo infrastructure provider for local development and portfolio demos."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime

from app.infrastructure.providers.base import InfrastructureProvider, InfrastructureSnapshot


class DemoProvider(InfrastructureProvider):
    """Generate realistic enterprise Kubernetes infrastructure without a live cluster."""

    source = "demo"

    def __init__(self, profile: str = "enterprise", cluster_name: str | None = None):
        self.profile = profile
        self.cluster_name = cluster_name

    def discover(self) -> InfrastructureSnapshot:
        """Return the default demo cluster; use `discover_all` for the full environment."""
        snapshots = self.discover_all()
        if self.cluster_name:
            for snapshot in snapshots:
                if snapshot.cluster["name"] == self.cluster_name:
                    return snapshot
        return snapshots[0]

    def discover_all(self) -> list[InfrastructureSnapshot]:
        now = datetime.now(UTC).isoformat()
        clusters = [
            self._cluster(
                name="prod-us-east-1",
                display_name="Production US East",
                region="us-east-1",
                environment="production",
                node_count=6,
                degraded=False,
                generated_at=now,
            ),
            self._cluster(
                name="staging-central",
                display_name="Staging Central",
                region="us-central1",
                environment="staging",
                node_count=3,
                degraded=True,
                generated_at=now,
            ),
            self._cluster(
                name="platform-monitoring",
                display_name="Platform Monitoring",
                region="eu-west-1",
                environment="shared-services",
                node_count=4,
                degraded=False,
                generated_at=now,
                include_observability=True,
            ),
        ]
        return [InfrastructureSnapshot(**cluster) for cluster in clusters]

    def _cluster(
        self,
        *,
        name: str,
        display_name: str,
        region: str,
        environment: str,
        node_count: int,
        degraded: bool,
        generated_at: str,
        include_observability: bool = False,
    ) -> dict:
        namespaces = [
            {"name": "platform", "status": "Active", "labels": {"team": "platform"}},
            {"name": "payments", "status": "Active", "labels": {"team": "payments"}},
            {"name": "edge", "status": "Active", "labels": {"team": "network"}},
        ]
        if include_observability:
            namespaces.append({"name": "observability", "status": "Active", "labels": {"team": "sre"}})

        nodes = [
            {
                "name": f"{name}-node-{idx}",
                "status": "NotReady" if degraded and idx == node_count else "Ready",
                "role": "control-plane" if idx == 1 else "worker",
                "kubernetes_version": "v1.29.3",
                "os_image": "Ubuntu 22.04 LTS",
                "container_runtime": "containerd://1.7.15",
                "cpu_allocatable": 4.0,
                "memory_allocatable_gb": 16.0,
                "cpu_usage_percent": 88.0 if degraded and idx == node_count else 54.0 + idx,
                "memory_usage_percent": 91.0 if degraded and idx == node_count else 61.0 + idx,
                "conditions": {"Ready": "False" if degraded and idx == node_count else "True"},
                "labels": {"topology.kubernetes.io/region": region, "nodepool": "general"},
            }
            for idx in range(1, node_count + 1)
        ]

        deployments = [
            self._deployment("platform", "api-gateway", "ghcr.io/nexusops/api-gateway:v3.2.1", 4, 4),
            self._deployment("platform", "auth-service", "ghcr.io/nexusops/auth-service:v2.8.0", 3, 3),
            self._deployment("payments", "payment-service", "ghcr.io/nexusops/payment-service:v4.1.7", 4, 2 if degraded else 4),
            self._deployment("payments", "ledger-worker", "ghcr.io/nexusops/ledger-worker:v1.9.2", 2, 2),
            self._deployment("edge", "cdn-controller", "ghcr.io/nexusops/cdn-controller:v1.14.0", 3, 3),
        ]
        if include_observability:
            deployments.extend(
                [
                    self._deployment("observability", "prometheus", "prom/prometheus:v2.52.0", 2, 2),
                    self._deployment("observability", "loki", "grafana/loki:3.0.0", 2, 2),
                    self._deployment("observability", "otel-collector", "otel/opentelemetry-collector-contrib:0.99.0", 3, 3),
                ]
            )

        replicasets = []
        pods = []
        services = []
        for deployment in deployments:
            rs_name = f"{deployment['name']}-7d9f6c"
            replicasets.append(
                {
                    "namespace_name": deployment["namespace_name"],
                    "name": rs_name,
                    "owner_kind": "Deployment",
                    "owner_name": deployment["name"],
                    "replicas_desired": deployment["replicas_desired"],
                    "replicas_ready": deployment["replicas_ready"],
                    "labels": deployment["labels"],
                    "selector": deployment["selector"],
                }
            )
            for idx in range(1, deployment["replicas_desired"] + 1):
                unhealthy = deployment["replicas_ready"] < idx
                pods.append(
                    {
                        "namespace_name": deployment["namespace_name"],
                        "name": f"{deployment['name']}-{idx}",
                        "phase": "Running" if not unhealthy else "CrashLoopBackOff",
                        "status": "Ready" if not unhealthy else "CrashLoopBackOff",
                        "node_name": nodes[(idx - 1) % len(nodes)]["name"],
                        "pod_ip": f"10.{len(pods) % 250}.{idx}.12",
                        "restart_count": 0 if not unhealthy else 17 + idx,
                        "ready": not unhealthy,
                        "owner_kind": "ReplicaSet",
                        "owner_name": rs_name,
                        "containers": [{"name": deployment["name"], "image": deployment["image"]}],
                        "labels": deployment["labels"],
                        "annotations": {"demo.nexusops.ai/generated-at": generated_at},
                    }
                )
            services.append(
                {
                    "namespace_name": deployment["namespace_name"],
                    "name": deployment["name"],
                    "service_type": "ClusterIP",
                    "cluster_ip": f"172.20.{len(services)}.10",
                    "external_ip": None,
                    "ports": [{"name": "http", "port": 80, "target_port": 8080}],
                    "selector": deployment["selector"],
                    "labels": deployment["labels"],
                }
            )

        return {
            "cluster": {
                "name": name,
                "display_name": display_name,
                "provider": "demo",
                "status": "degraded" if degraded else "connected",
                "region": region,
                "environment": environment,
                "kubernetes_version": "v1.29.3",
                "api_server_url": f"https://{name}.demo.nexusops.local",
                "tags": {"source": "demo", "profile": self.profile},
                "metadata": {"generated_at": generated_at, "source": "demo"},
            },
            "nodes": nodes,
            "namespaces": namespaces,
            "deployments": deployments,
            "workloads": deepcopy(deployments),
            "replicasets": replicasets,
            "pods": pods,
            "services": services,
        }

    def _deployment(
        self,
        namespace: str,
        name: str,
        image: str,
        replicas: int,
        ready: int,
    ) -> dict:
        labels = {"app": name, "app.kubernetes.io/name": name}
        return {
            "namespace_name": namespace,
            "name": name,
            "kind": "Deployment",
            "replicas_desired": replicas,
            "replicas_ready": ready,
            "image": image,
            "cpu_request_millicores": 250,
            "memory_request_mb": 512,
            "cpu_limit_millicores": 1000,
            "memory_limit_mb": 1024,
            "cpu_usage_percent": 72.0 if ready < replicas else 48.0,
            "memory_usage_percent": 88.0 if ready < replicas else 55.0,
            "labels": labels,
            "annotations": {"demo.nexusops.ai/source": "DemoProvider"},
            "selector": {"app": name},
            "is_healthy": ready >= replicas,
        }
