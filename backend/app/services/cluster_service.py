"""
NexusOps AI — Cluster Service
Business logic for cluster management and synchronization
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from app.models.cluster import (
    Cluster,
    ClusterStatus,
    KubernetesPod,
    KubernetesService,
    KubernetesWorkload,
)
from app.repositories.cluster_repository import ClusterRepository
from app.schemas.cluster import ClusterCreate, ClusterUpdate

logger = structlog.get_logger(__name__)


class ClusterService:
    """
    Handles cluster registration, lifecycle, and resource synchronization.
    Orchestrates between the Kubernetes client and the persistence layer.
    """

    def __init__(self, repository: ClusterRepository):
        self.repo = repository

    async def register_cluster(self, data: ClusterCreate) -> Cluster:
        """Register a new cluster in the platform."""
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise ValueError(f"Cluster '{data.name}' is already registered.")

        cluster = Cluster(
            id=str(uuid.uuid4()),
            name=data.name,
            display_name=data.display_name,
            provider=data.provider,
            region=data.region,
            environment=data.environment,
            api_server_url=data.api_server_url,
            tags=data.tags or {},
            status=ClusterStatus.UNKNOWN,
        )

        created = await self.repo.create(cluster)
        logger.info("Cluster registered", cluster_id=created.id, cluster_name=created.name)
        return created

    async def get_cluster(self, cluster_id: str) -> Optional[Cluster]:
        return await self.repo.get_with_nodes(cluster_id)

    async def list_clusters(
        self,
        skip: int = 0,
        limit: int = 50,
        active_only: bool = True,
    ) -> tuple[List[Cluster], int]:
        filters = {"is_active": True} if active_only else None
        clusters = await self.repo.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.repo.count(filters=filters)
        return list(clusters), total

    async def update_cluster(self, cluster_id: str, data: ClusterUpdate) -> Optional[Cluster]:
        cluster = await self.repo.get(cluster_id)
        if not cluster:
            return None
        updates = data.model_dump(exclude_none=True)
        return await self.repo.update(cluster, updates)

    async def delete_cluster(self, cluster_id: str) -> bool:
        cluster = await self.repo.get(cluster_id)
        if not cluster:
            return False
        await self.repo.delete(cluster)
        logger.info("Cluster deleted", cluster_id=cluster_id)
        return True

    async def sync_cluster_resources(
        self,
        cluster_id: str,
        k8s_data: Dict[str, Any],
    ) -> Cluster:
        """
        Synchronize live Kubernetes resource data into the platform.
        Called by the Celery sync task after fetching from the K8s API.
        """
        cluster = await self.repo.get(cluster_id)
        if not cluster:
            raise ValueError(f"Cluster {cluster_id} not found.")

        from datetime import datetime, timezone

        cluster.node_count = k8s_data.get("node_count", 0)
        cluster.namespace_count = k8s_data.get("namespace_count", 0)
        cluster.pod_count = k8s_data.get("pod_count", 0)
        cluster.kubernetes_version = k8s_data.get("kubernetes_version")
        cluster.cpu_capacity = k8s_data.get("cpu_capacity")
        cluster.memory_capacity_gb = k8s_data.get("memory_capacity_gb")
        cluster.status = ClusterStatus.CONNECTED
        cluster.last_sync_at = datetime.now(timezone.utc)

        await self.repo.save(cluster)
        logger.info("Cluster synced", cluster_id=cluster_id, pod_count=cluster.pod_count)
        return cluster

    async def discover_and_sync_cluster(self, cluster_id: str) -> Cluster:
        """Run provider-based infrastructure discovery and persist the full topology."""
        from app.services.infrastructure_discovery_service import InfrastructureDiscoveryService

        discovery = InfrastructureDiscoveryService(repository=self.repo)
        return await discovery.sync_cluster(cluster_id)

    async def update_cluster_status(
        self,
        cluster_id: str,
        status: ClusterStatus,
    ) -> None:
        cluster = await self.repo.get(cluster_id)
        if cluster:
            cluster.status = status
            await self.repo.save(cluster)

    async def get_workloads(
        self,
        cluster_id: str,
        namespace: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[KubernetesWorkload]:
        workloads = await self.repo.get_workloads(cluster_id, namespace, skip, limit)
        return list(workloads)

    async def get_deployments(
        self,
        cluster_id: str,
        namespace: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[KubernetesWorkload]:
        workloads = await self.repo.get_workloads(cluster_id, namespace, skip, limit)
        return [w for w in workloads if w.kind == "Deployment"]

    async def get_namespaces(self, cluster_id: str):
        return list(await self.repo.get_namespaces(cluster_id))

    async def get_nodes(self, cluster_id: str):
        return list(await self.repo.get_nodes(cluster_id))

    async def get_pods(
        self,
        cluster_id: str,
        namespace: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> List[KubernetesPod]:
        return list(await self.repo.get_pods(cluster_id, namespace, skip, limit))

    async def get_services(
        self,
        cluster_id: str,
        namespace: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> List[KubernetesService]:
        return list(await self.repo.get_services(cluster_id, namespace, skip, limit))

    async def get_replicasets(
        self,
        cluster_id: str,
        namespace: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ):
        return list(await self.repo.get_replicasets(cluster_id, namespace, skip, limit))

    async def get_topology(self, cluster_id: str) -> Dict[str, Any]:
        cluster = await self.repo.get_with_topology(cluster_id)
        if not cluster:
            return {}

        workload_children = {}
        for workload in cluster.workloads:
            workload_children[(workload.namespace_name, workload.name)] = {
                "id": workload.id,
                "name": workload.name,
                "type": workload.kind.lower(),
                "status": "healthy" if workload.is_healthy else "degraded",
                "metadata": {
                    "replicas_ready": workload.replicas_ready,
                    "replicas_desired": workload.replicas_desired,
                    "image": workload.image,
                },
                "children": [],
            }

        replicasets_by_name = {(rs.namespace_name, rs.name): rs for rs in cluster.replicasets}
        for pod in cluster.pods:
            workload_key = None
            if pod.workload_id:
                workload = next((w for w in cluster.workloads if w.id == pod.workload_id), None)
                if workload:
                    workload_key = (workload.namespace_name, workload.name)
            elif pod.owner_kind == "ReplicaSet" and pod.owner_name:
                owner = replicasets_by_name.get((pod.namespace_name, pod.owner_name))
                if owner and owner.owner_name:
                    workload_key = (pod.namespace_name, owner.owner_name)

            pod_node = {
                "id": pod.id,
                "name": pod.name,
                "type": "pod",
                "status": pod.status,
                "metadata": {
                    "phase": pod.phase,
                    "ready": pod.ready,
                    "restart_count": pod.restart_count,
                    "node_name": pod.node_name,
                },
                "children": [],
            }
            if workload_key and workload_key in workload_children:
                workload_children[workload_key]["children"].append(pod_node)

        namespace_nodes = []
        for namespace in cluster.namespaces:
            children = [
                node
                for (namespace_name, _), node in workload_children.items()
                if namespace_name == namespace.name
            ]
            services = [
                {
                    "id": service.id,
                    "name": service.name,
                    "type": "service",
                    "status": service.service_type,
                    "metadata": {"cluster_ip": service.cluster_ip, "ports": service.ports or []},
                    "children": [],
                }
                for service in cluster.services
                if service.namespace_name == namespace.name
            ]
            namespace_nodes.append(
                {
                    "id": namespace.id,
                    "name": namespace.name,
                    "type": "namespace",
                    "status": namespace.status,
                    "metadata": {"services": len(services)},
                    "children": children + services,
                }
            )

        return {
            "cluster_id": cluster.id,
            "generated_at": datetime.now(timezone.utc),
            "root": {
                "id": cluster.id,
                "name": cluster.name,
                "type": "cluster",
                "status": cluster.status,
                "metadata": {
                    "provider": cluster.provider,
                    "nodes": cluster.node_count,
                    "version": cluster.kubernetes_version,
                },
                "children": namespace_nodes,
            },
        }

    async def get_cluster_summary(self, cluster_id: str) -> Dict[str, Any]:
        """Get a high-level health and resource summary for dashboard display."""
        cluster = await self.repo.get_with_nodes(cluster_id)
        if not cluster:
            return {}

        unhealthy_nodes = [n for n in cluster.nodes if n.status != "Ready"]

        return {
            "cluster_id": cluster_id,
            "name": cluster.name,
            "status": cluster.status,
            "node_count": cluster.node_count,
            "unhealthy_nodes": len(unhealthy_nodes),
            "pod_count": cluster.pod_count,
            "namespace_count": cluster.namespace_count,
            "cpu_capacity": cluster.cpu_capacity,
            "memory_capacity_gb": cluster.memory_capacity_gb,
            "last_sync_at": cluster.last_sync_at,
        }
