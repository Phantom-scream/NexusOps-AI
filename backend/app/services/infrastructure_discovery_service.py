"""Infrastructure discovery and ingestion service."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

import structlog

from app.infrastructure.providers import DemoProvider, InfrastructureProvider, InfrastructureSnapshot, KubernetesProvider
from app.models.cluster import (
    Cluster,
    ClusterNode,
    ClusterStatus,
    KubernetesNamespace,
    KubernetesPod,
    KubernetesReplicaSet,
    KubernetesService,
    KubernetesWorkload,
)
from app.repositories.cluster_repository import ClusterRepository

logger = structlog.get_logger(__name__)


class InfrastructureDiscoveryService:
    """Coordinates provider discovery and persistence into the domain model."""

    def __init__(self, repository: ClusterRepository):
        self.repo = repository

    async def sync_cluster(self, cluster_id: str, provider: Optional[InfrastructureProvider] = None) -> Cluster:
        cluster = await self.repo.get(cluster_id)
        if not cluster:
            raise ValueError(f"Cluster {cluster_id} not found")

        provider = provider or self._provider_for_cluster(cluster)
        snapshot = provider.discover()
        synced = await self.ingest_snapshot(snapshot, existing_cluster=cluster)
        logger.info("Infrastructure sync completed", cluster_id=synced.id, provider=provider.source)
        return synced

    async def generate_demo_environment(self) -> list[Cluster]:
        provider = DemoProvider()
        clusters = []
        for snapshot in provider.discover_all():
            clusters.append(await self.ingest_snapshot(snapshot))
        logger.info("Demo infrastructure generated", clusters=len(clusters))
        return clusters

    async def ingest_snapshot(
        self,
        snapshot: InfrastructureSnapshot,
        existing_cluster: Optional[Cluster] = None,
    ) -> Cluster:
        cluster = existing_cluster or await self.repo.get_by_name(snapshot.cluster["name"])
        if not cluster:
            cluster = Cluster(id=str(uuid4()), name=snapshot.cluster["name"], display_name=snapshot.cluster["display_name"])
            self.repo.session.add(cluster)

        cluster.display_name = snapshot.cluster.get("display_name") or cluster.name
        cluster.provider = snapshot.cluster.get("provider") or cluster.provider
        cluster.status = snapshot.cluster.get("status") or ClusterStatus.CONNECTED
        cluster.region = snapshot.cluster.get("region")
        cluster.environment = snapshot.cluster.get("environment") or cluster.environment
        cluster.api_server_url = snapshot.cluster.get("api_server_url")
        cluster.kubernetes_version = snapshot.cluster.get("kubernetes_version")
        cluster.cpu_capacity = snapshot.cluster.get("cpu_capacity") or self._sum(snapshot.nodes, "cpu_allocatable")
        cluster.memory_capacity_gb = snapshot.cluster.get("memory_capacity_gb") or self._sum(snapshot.nodes, "memory_allocatable_gb")
        cluster.node_count = len(snapshot.nodes)
        cluster.namespace_count = len(snapshot.namespaces)
        cluster.pod_count = len(snapshot.pods)
        cluster.service_count = len(snapshot.services)
        cluster.deployment_count = len(snapshot.deployments)
        cluster.tags = snapshot.cluster.get("tags") or {}
        cluster.metadata_ = snapshot.cluster.get("metadata") or {}
        cluster.is_active = True
        cluster.last_sync_at = datetime.now(timezone.utc)

        await self.repo.session.flush()

        namespaces = [
            KubernetesNamespace(
                cluster_id=cluster.id,
                name=item["name"],
                status=item.get("status", "Active"),
                labels=item.get("labels") or {},
                annotations=item.get("annotations") or {},
                resource_quota=item.get("resource_quota"),
            )
            for item in snapshot.namespaces
        ]
        nodes = [
            ClusterNode(
                cluster_id=cluster.id,
                name=item["name"],
                status=item.get("status", "Ready"),
                role=item.get("role", "worker"),
                kubernetes_version=item.get("kubernetes_version"),
                os_image=item.get("os_image"),
                container_runtime=item.get("container_runtime"),
                cpu_allocatable=item.get("cpu_allocatable"),
                memory_allocatable_gb=item.get("memory_allocatable_gb"),
                cpu_usage_percent=item.get("cpu_usage_percent"),
                memory_usage_percent=item.get("memory_usage_percent"),
                conditions=item.get("conditions") or {},
                labels=item.get("labels") or {},
            )
            for item in snapshot.nodes
        ]
        workloads = [
            KubernetesWorkload(
                cluster_id=cluster.id,
                namespace_name=item["namespace_name"],
                name=item["name"],
                kind=item.get("kind", "Deployment"),
                replicas_desired=item.get("replicas_desired", 1),
                replicas_ready=item.get("replicas_ready", 0),
                image=item.get("image"),
                cpu_request_millicores=item.get("cpu_request_millicores"),
                memory_request_mb=item.get("memory_request_mb"),
                cpu_limit_millicores=item.get("cpu_limit_millicores"),
                memory_limit_mb=item.get("memory_limit_mb"),
                cpu_usage_percent=item.get("cpu_usage_percent"),
                memory_usage_percent=item.get("memory_usage_percent"),
                labels=item.get("labels") or {},
                annotations=item.get("annotations") or {},
                manifest=item.get("manifest"),
                selector=item.get("selector") or {},
                is_healthy=item.get("is_healthy", item.get("replicas_ready", 0) >= item.get("replicas_desired", 1)),
            )
            for item in snapshot.workloads
        ]
        replicasets = [
            KubernetesReplicaSet(
                cluster_id=cluster.id,
                namespace_name=item["namespace_name"],
                name=item["name"],
                owner_kind=item.get("owner_kind"),
                owner_name=item.get("owner_name"),
                replicas_desired=item.get("replicas_desired", 0),
                replicas_ready=item.get("replicas_ready", 0),
                labels=item.get("labels") or {},
                selector=item.get("selector") or {},
            )
            for item in snapshot.replicasets
        ]
        pods = [
            KubernetesPod(
                cluster_id=cluster.id,
                namespace_name=item["namespace_name"],
                name=item["name"],
                phase=item.get("phase", "Unknown"),
                status=item.get("status", item.get("phase", "Unknown")),
                node_name=item.get("node_name"),
                pod_ip=item.get("pod_ip"),
                restart_count=item.get("restart_count", 0),
                ready=item.get("ready", False),
                owner_kind=item.get("owner_kind"),
                owner_name=item.get("owner_name"),
                containers=item.get("containers") or [],
                labels=item.get("labels") or {},
                annotations=item.get("annotations") or {},
                started_at=item.get("started_at"),
            )
            for item in snapshot.pods
        ]
        services = [
            KubernetesService(
                cluster_id=cluster.id,
                namespace_name=item["namespace_name"],
                name=item["name"],
                service_type=item.get("service_type", "ClusterIP"),
                cluster_ip=item.get("cluster_ip"),
                external_ip=item.get("external_ip"),
                ports=item.get("ports") or [],
                selector=item.get("selector") or {},
                labels=item.get("labels") or {},
                annotations=item.get("annotations") or {},
            )
            for item in snapshot.services
        ]

        await self.repo.replace_infrastructure(
            cluster=cluster,
            namespaces=namespaces,
            nodes=nodes,
            workloads=workloads,
            replicasets=replicasets,
            pods=pods,
            services=services,
        )
        return cluster

    def _provider_for_cluster(self, cluster: Cluster) -> InfrastructureProvider:
        if cluster.provider == "demo" or (cluster.tags or {}).get("source") == "demo":
            return DemoProvider(cluster_name=cluster.name)
        return KubernetesProvider(cluster=cluster, context=(cluster.metadata_ or {}).get("kube_context"))

    def _sum(self, rows: list[dict], key: str) -> float:
        return float(sum(row.get(key) or 0 for row in rows))
