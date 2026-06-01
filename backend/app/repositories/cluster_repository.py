"""
NexusOps AI — Cluster Repository
"""
from typing import List, Optional, Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.models.cluster import (
    Cluster,
    ClusterNode,
    KubernetesNamespace,
    KubernetesPod,
    KubernetesReplicaSet,
    KubernetesService,
    KubernetesWorkload,
)
from app.repositories.base import BaseRepository


class ClusterRepository(BaseRepository[Cluster]):

    async def get_by_name(self, name: str) -> Optional[Cluster]:
        result = await self.session.execute(
            select(Cluster).where(Cluster.name == name)
        )
        return result.scalar_one_or_none()

    async def get_with_nodes(self, cluster_id: str) -> Optional[Cluster]:
        result = await self.session.execute(
            select(Cluster)
            .where(Cluster.id == cluster_id)
            .options(selectinload(Cluster.nodes))
        )
        return result.scalar_one_or_none()

    async def get_with_topology(self, cluster_id: str) -> Optional[Cluster]:
        result = await self.session.execute(
            select(Cluster)
            .where(Cluster.id == cluster_id)
            .options(
                selectinload(Cluster.nodes),
                selectinload(Cluster.namespaces),
                selectinload(Cluster.workloads),
                selectinload(Cluster.pods),
                selectinload(Cluster.services),
                selectinload(Cluster.replicasets),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_clusters(self) -> Sequence[Cluster]:
        result = await self.session.execute(
            select(Cluster).where(Cluster.is_active == True).order_by(Cluster.name)
        )
        return result.scalars().all()

    async def get_workloads(
        self,
        cluster_id: str,
        namespace: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[KubernetesWorkload]:
        stmt = select(KubernetesWorkload).where(KubernetesWorkload.cluster_id == cluster_id)
        if namespace:
            stmt = stmt.where(KubernetesWorkload.namespace_name == namespace)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_namespaces(self, cluster_id: str) -> Sequence[KubernetesNamespace]:
        result = await self.session.execute(
            select(KubernetesNamespace)
            .where(KubernetesNamespace.cluster_id == cluster_id)
            .order_by(KubernetesNamespace.name)
        )
        return result.scalars().all()

    async def get_nodes(self, cluster_id: str) -> Sequence[ClusterNode]:
        result = await self.session.execute(
            select(ClusterNode).where(ClusterNode.cluster_id == cluster_id).order_by(ClusterNode.name)
        )
        return result.scalars().all()

    async def get_pods(
        self,
        cluster_id: str,
        namespace: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> Sequence[KubernetesPod]:
        stmt = select(KubernetesPod).where(KubernetesPod.cluster_id == cluster_id)
        if namespace:
            stmt = stmt.where(KubernetesPod.namespace_name == namespace)
        stmt = stmt.order_by(KubernetesPod.namespace_name, KubernetesPod.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_services(
        self,
        cluster_id: str,
        namespace: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> Sequence[KubernetesService]:
        stmt = select(KubernetesService).where(KubernetesService.cluster_id == cluster_id)
        if namespace:
            stmt = stmt.where(KubernetesService.namespace_name == namespace)
        stmt = stmt.order_by(KubernetesService.namespace_name, KubernetesService.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_replicasets(
        self,
        cluster_id: str,
        namespace: Optional[str] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> Sequence[KubernetesReplicaSet]:
        stmt = select(KubernetesReplicaSet).where(KubernetesReplicaSet.cluster_id == cluster_id)
        if namespace:
            stmt = stmt.where(KubernetesReplicaSet.namespace_name == namespace)
        stmt = stmt.order_by(KubernetesReplicaSet.namespace_name, KubernetesReplicaSet.name).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def replace_infrastructure(
        self,
        cluster: Cluster,
        namespaces: list[KubernetesNamespace],
        nodes: list[ClusterNode],
        workloads: list[KubernetesWorkload],
        replicasets: list[KubernetesReplicaSet],
        pods: list[KubernetesPod],
        services: list[KubernetesService],
    ) -> Cluster:
        """Replace a cluster's discovered topology with a fresh provider snapshot."""
        for model in (
            KubernetesPod,
            KubernetesService,
            KubernetesReplicaSet,
            KubernetesWorkload,
            ClusterNode,
            KubernetesNamespace,
        ):
            await self.session.execute(delete(model).where(model.cluster_id == cluster.id))

        for namespace in namespaces:
            namespace.cluster_id = cluster.id
        self.session.add_all(namespaces)
        await self.session.flush()
        namespace_ids = {ns.name: ns.id for ns in namespaces}

        for node in nodes:
            node.cluster_id = cluster.id
        self.session.add_all(nodes)

        for workload in workloads:
            workload.cluster_id = cluster.id
            workload.namespace_id = namespace_ids.get(workload.namespace_name)
        self.session.add_all(workloads)
        await self.session.flush()

        workload_ids = {
            (workload.namespace_name, workload.kind, workload.name): workload.id
            for workload in workloads
        }

        for replicaset in replicasets:
            replicaset.cluster_id = cluster.id
            replicaset.namespace_id = namespace_ids.get(replicaset.namespace_name)
            if replicaset.owner_kind == "Deployment" and replicaset.owner_name:
                replicaset.workload_id = workload_ids.get(
                    (replicaset.namespace_name, "Deployment", replicaset.owner_name)
                )

        for pod in pods:
            pod.cluster_id = cluster.id
            pod.namespace_id = namespace_ids.get(pod.namespace_name)
            if pod.owner_kind == "ReplicaSet" and pod.owner_name:
                owner = next(
                    (
                        rs
                        for rs in replicasets
                        if rs.namespace_name == pod.namespace_name and rs.name == pod.owner_name
                    ),
                    None,
                )
                if owner and owner.owner_kind == "Deployment" and owner.owner_name:
                    pod.workload_id = workload_ids.get(
                        (pod.namespace_name, "Deployment", owner.owner_name)
                    )
            elif pod.owner_kind in {"Deployment", "StatefulSet", "DaemonSet"} and pod.owner_name:
                pod.workload_id = workload_ids.get(
                    (pod.namespace_name, pod.owner_kind, pod.owner_name)
                )

        for service in services:
            service.cluster_id = cluster.id
            service.namespace_id = namespace_ids.get(service.namespace_name)

        self.session.add_all(replicasets)
        self.session.add_all(pods)
        self.session.add_all(services)
        await self.session.flush()
        await self.session.refresh(cluster)
        return cluster
