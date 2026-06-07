"""
NexusOps AI — Cluster Sync Celery Tasks
Periodic tasks to keep cluster state fresh
"""
import asyncio

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
    from app.models.cluster import ClusterStatus
    from app.repositories.cluster_repository import ClusterRepository
    from app.services.infrastructure_discovery_service import InfrastructureDiscoveryService

    logger.info("Starting cluster sync", cluster_id=cluster_id)

    async with AsyncSessionLocal() as session:
        repo = ClusterRepository(model=__import__("app.models.cluster", fromlist=["Cluster"]).Cluster, session=session)
        service = InfrastructureDiscoveryService(repository=repo)

        cluster = await repo.get(cluster_id)
        if not cluster:
            logger.warning("Cluster not found for sync", cluster_id=cluster_id)
            return {"status": "not_found"}

        try:
            synced = await service.sync_cluster(cluster_id)
            await session.commit()

            logger.info(
                "Cluster sync complete",
                cluster_id=cluster_id,
                pod_count=synced.pod_count,
            )
            return {"status": "success", "cluster_id": cluster_id}

        except Exception as exc:
            logger.error("Cluster sync failed", cluster_id=cluster_id, error=str(exc))
            cluster.status = ClusterStatus.DEGRADED
            await repo.save(cluster)
            await session.commit()
            return {"status": "error", "error": str(exc)}


async def _sync_all_clusters_async() -> dict:
    from app.core.database import AsyncSessionLocal
    from app.models.cluster import Cluster
    from app.repositories.cluster_repository import ClusterRepository

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
