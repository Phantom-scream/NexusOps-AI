"""
NexusOps AI — Cluster Repository
"""
from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.cluster import Cluster, KubernetesWorkload
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
