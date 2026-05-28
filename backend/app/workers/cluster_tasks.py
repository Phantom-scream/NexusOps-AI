"""
NexusOps AI — Cluster Sync Celery Tasks
Periodic tasks to keep cluster state fresh
"""
import asyncio
from typing import Optional

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


def run_async(coro):
    """Run async coroutine from sync Celery task context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.workers.cluster_tasks.sync_cluster",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def sync_cluster(self, cluster_id: str) -> dict:
    """Sync a single cluster's resources from the Kubernetes API."""
    return run_async(_sync_cluster_async(cluster_id))


@celery_app.task(
    name="app.workers.cluster_tasks.sync_all_active_clusters",
    bind=True,
)
def sync_all_active_clusters(self) -> dict:
    """Periodic task: sync all active registered clusters."""
    return run_async(_sync_all_clusters_async())


async def _sync_cluster_async(cluster_id: str) -> dict:
    from app.core.database import AsyncSessionLocal
    from app.repositories.cluster_repository import ClusterRepository
    from app.services.cluster_service import ClusterService
    from app.infrastructure.kubernetes_client import KubernetesClient
    from app.models.cluster import ClusterStatus

    logger.info("Starting cluster sync", cluster_id=cluster_id)

    async with AsyncSessionLocal() as session:
        repo = ClusterRepository(model=__import__("app.models.cluster", fromlist=["Cluster"]).Cluster, session=session)
        service = ClusterService(repository=repo)

        cluster = await service.get_cluster(cluster_id)
        if not cluster:
            logger.warning("Cluster not found for sync", cluster_id=cluster_id)
            return {"status": "not_found"}

        try:
            k8s_client = KubernetesClient()
            k8s_data = k8s_client.get_cluster_info()

            await service.sync_cluster_resources(cluster_id, k8s_data)
            await session.commit()

            logger.info(
                "Cluster sync complete",
                cluster_id=cluster_id,
                pod_count=k8s_data.get("pod_count", 0),
            )
            return {"status": "success", "cluster_id": cluster_id}

        except Exception as exc:
            logger.error("Cluster sync failed", cluster_id=cluster_id, error=str(exc))
            await service.update_cluster_status(cluster_id, ClusterStatus.DEGRADED)
            await session.commit()
            return {"status": "error", "error": str(exc)}


async def _sync_all_clusters_async() -> dict:
    from app.core.database import AsyncSessionLocal
    from app.repositories.cluster_repository import ClusterRepository
    from app.models.cluster import Cluster

    async with AsyncSessionLocal() as session:
        repo = ClusterRepository(model=Cluster, session=session)
        active_clusters = await repo.get_active_clusters()

    results = []
    for cluster in active_clusters:
        try:
            result = await _sync_cluster_async(cluster.id)
            results.append(result)
        except Exception as exc:
            logger.error("Failed to sync cluster", cluster_id=cluster.id, error=str(exc))
            results.append({"status": "error", "cluster_id": cluster.id})

    synced = sum(1 for r in results if r.get("status") == "success")
    logger.info("Batch cluster sync complete", total=len(results), synced=synced)
    return {"synced": synced, "total": len(results)}
