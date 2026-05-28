"""
NexusOps AI — Clusters API
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.models.cluster import Cluster
from app.repositories.cluster_repository import ClusterRepository
from app.schemas.cluster import (
    ClusterCreate,
    ClusterDetailOut,
    ClusterListResponse,
    ClusterOut,
    ClusterUpdate,
    WorkloadOut,
)
from app.services.cluster_service import ClusterService

router = APIRouter()


def get_cluster_service(db: AsyncSession = Depends(get_db)) -> ClusterService:
    return ClusterService(repository=ClusterRepository(model=Cluster, session=db))


@router.get("", response_model=ClusterListResponse)
async def list_clusters(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    active_only: bool = Query(default=True),
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List all registered clusters with pagination."""
    skip = (page - 1) * page_size
    clusters, total = await service.list_clusters(skip=skip, limit=page_size, active_only=active_only)
    return ClusterListResponse(
        items=[ClusterOut.model_validate(c) for c in clusters],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ClusterOut, status_code=status.HTTP_201_CREATED)
async def register_cluster(
    data: ClusterCreate,
    service: ClusterService = Depends(get_cluster_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Register a new Kubernetes cluster."""
    if not current_user.is_operator:
        raise HTTPException(status_code=403, detail="Operator role required")
    try:
        cluster = await service.register_cluster(data)
        return ClusterOut.model_validate(cluster)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/{cluster_id}", response_model=ClusterDetailOut)
async def get_cluster(
    cluster_id: str,
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get cluster details with node information."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return ClusterDetailOut.model_validate(cluster)


@router.patch("/{cluster_id}", response_model=ClusterOut)
async def update_cluster(
    cluster_id: str,
    data: ClusterUpdate,
    service: ClusterService = Depends(get_cluster_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update cluster metadata."""
    if not current_user.is_operator:
        raise HTTPException(status_code=403, detail="Operator role required")
    cluster = await service.update_cluster(cluster_id, data)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return ClusterOut.model_validate(cluster)


@router.delete("/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(
    cluster_id: str,
    service: ClusterService = Depends(get_cluster_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Deregister a cluster."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin role required")
    deleted = await service.delete_cluster(cluster_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cluster not found")


@router.post("/{cluster_id}/sync", status_code=status.HTTP_202_ACCEPTED)
async def trigger_cluster_sync(
    cluster_id: str,
    service: ClusterService = Depends(get_cluster_service),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Trigger an asynchronous cluster resource sync."""
    if not current_user.is_operator:
        raise HTTPException(status_code=403, detail="Operator role required")

    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    from app.workers.cluster_tasks import sync_cluster
    task = sync_cluster.delay(cluster_id)

    return {"task_id": task.id, "status": "queued", "cluster_id": cluster_id}


@router.get("/{cluster_id}/workloads", response_model=list[WorkloadOut])
async def get_cluster_workloads(
    cluster_id: str,
    namespace: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=200),
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List workloads in a cluster, optionally filtered by namespace."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    workloads = await service.get_workloads(cluster_id, namespace, skip, limit)
    return [WorkloadOut.model_validate(w) for w in workloads]


@router.get("/{cluster_id}/summary")
async def get_cluster_summary(
    cluster_id: str,
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get a high-level cluster health summary for the dashboard."""
    return await service.get_cluster_summary(cluster_id)
