"""Telemetry ingestion Celery tasks."""

import asyncio

import structlog

from app.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.telemetry_tasks.generate_demo_telemetry", bind=True)
def generate_demo_telemetry(self) -> dict:
    """Generate demo telemetry for local development and portfolio demos."""
    _ = self
    return run_async(_generate_demo_telemetry_async())


async def _generate_demo_telemetry_async() -> dict:
    from app.core.database import AsyncSessionLocal
    from app.models.cluster import Cluster
    from app.models.telemetry import TelemetrySource
    from app.repositories.cluster_repository import ClusterRepository
    from app.repositories.telemetry_repository import TelemetryRepository
    from app.services.telemetry_service import TelemetryService

    async with AsyncSessionLocal() as session:
        service = TelemetryService(
            telemetry_repo=TelemetryRepository(model=TelemetrySource, session=session),
            cluster_repo=ClusterRepository(model=Cluster, session=session),
        )
        _, counts = await service.generate_demo_telemetry()
        await session.commit()
        logger.info("Demo telemetry task completed", **counts)
        return counts
