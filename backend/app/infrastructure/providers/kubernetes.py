"""Kubernetes-backed infrastructure provider."""

from typing import Optional

from app.infrastructure.kubernetes_client import KubernetesClient
from app.infrastructure.providers.base import InfrastructureProvider, InfrastructureSnapshot
from app.models.cluster import Cluster


class KubernetesProvider(InfrastructureProvider):
    """Discover infrastructure from a kubeconfig, Minikube, Kind, or in-cluster config."""

    source = "kubernetes"

    def __init__(
        self,
        cluster: Optional[Cluster] = None,
        kubeconfig_path: Optional[str] = None,
        context: Optional[str] = None,
    ):
        self.cluster = cluster
        self.client = KubernetesClient(kubeconfig_path=kubeconfig_path, context=context)

    def discover(self) -> InfrastructureSnapshot:
        info = self.client.get_cluster_info()
        workloads = self.client.get_workloads()
        deployments = [workload for workload in workloads if workload.get("kind") == "Deployment"]
        cluster_name = self.cluster.name if self.cluster else "kubernetes-cluster"

        return InfrastructureSnapshot(
            cluster={
                "name": cluster_name,
                "display_name": self.cluster.display_name if self.cluster else cluster_name,
                "provider": self.cluster.provider if self.cluster else "vanilla",
                "status": "connected",
                "region": self.cluster.region if self.cluster else None,
                "environment": self.cluster.environment if self.cluster else "production",
                "api_server_url": self.cluster.api_server_url if self.cluster else None,
                "kubernetes_version": info.get("kubernetes_version"),
                "cpu_capacity": info.get("cpu_capacity"),
                "memory_capacity_gb": info.get("memory_capacity_gb"),
                "tags": self.cluster.tags if self.cluster else {"source": self.source},
                "metadata": {"source": self.source},
            },
            nodes=info.get("nodes", []),
            namespaces=info.get("namespaces", []),
            deployments=deployments,
            workloads=workloads,
            replicasets=self.client.get_replicasets(),
            pods=self.client.get_pods(),
            services=self.client.get_services(),
        )
