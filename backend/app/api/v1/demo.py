"""Demo infrastructure API."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.models.cluster import Cluster
from app.repositories.cluster_repository import ClusterRepository
from app.schemas.cluster import ClusterOut
from app.services.infrastructure_discovery_service import InfrastructureDiscoveryService

router = APIRouter()


def get_discovery_service(db: AsyncSession = Depends(get_db)) -> InfrastructureDiscoveryService:
    return InfrastructureDiscoveryService(repository=ClusterRepository(model=Cluster, session=db))


@router.post("/generate", response_model=list[ClusterOut])
async def generate_demo_infrastructure(
    service: InfrastructureDiscoveryService = Depends(get_discovery_service),
    _: CurrentUser = Depends(get_current_user),
):
    """
    Generate a realistic demo infrastructure topology using the same persistence
    model and APIs as Kubernetes discovery.
    """
    clusters = await service.generate_demo_environment()
    return [ClusterOut.model_validate(cluster) for cluster in clusters]
