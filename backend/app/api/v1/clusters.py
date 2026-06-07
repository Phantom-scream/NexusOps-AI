"""
NexusOps AI — Clusters API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user, require_admin, require_operator
from app.models.audit import AuditEvent
from app.models.cluster import Cluster
from app.repositories.audit_repository import AuditRepository
from app.repositories.cluster_repository import ClusterRepository
from app.schemas.cluster import (
    ClusterCreate,
    ClusterDetailOut,
    ClusterListResponse,
    ClusterNodeOut,
    ClusterOut,
    ClusterTopologyOut,
    ClusterUpdate,
    NamespaceOut,
    PodOut,
    ReplicaSetOut,
    ServiceOut,
    SyncResponse,
    WorkloadOut,
)
from app.services.audit_service import AuditService
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
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: ClusterService = Depends(get_cluster_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Register a new Kubernetes cluster."""
    try:
        cluster = await service.register_cluster(data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="cluster.register",
        actor=current_user,
        request=request,
        resource_type="cluster",
        resource_id=cluster.id,
        metadata={"name": cluster.name, "provider": cluster.provider},
    )
    return ClusterOut.model_validate(cluster)


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
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: ClusterService = Depends(get_cluster_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Update cluster metadata."""
    cluster = await service.update_cluster(cluster_id, data)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="cluster.update",
        actor=current_user,
        request=request,
        resource_type="cluster",
        resource_id=cluster.id,
        metadata=data.model_dump(exclude_unset=True),
    )
    return ClusterOut.model_validate(cluster)


@router.delete("/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(
    cluster_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: ClusterService = Depends(get_cluster_service),
    current_user: CurrentUser = Depends(require_admin),
):
    """Deregister a cluster."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    deleted = await service.delete_cluster(cluster_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cluster not found")
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="cluster.delete",
        actor=current_user,
        request=request,
        resource_type="cluster",
        resource_id=cluster_id,
        metadata={"name": cluster.name, "provider": cluster.provider},
    )


@router.post("/{cluster_id}/sync", response_model=SyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_cluster_sync(
    cluster_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: ClusterService = Depends(get_cluster_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Trigger an asynchronous cluster resource sync."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    from app.workers.cluster_tasks import sync_cluster
    task = sync_cluster.delay(cluster_id)

    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="cluster.sync",
        actor=current_user,
        request=request,
        resource_type="cluster",
        resource_id=cluster_id,
        metadata={"task_id": task.id},
    )
    return SyncResponse(task_id=task.id, status="queued", cluster_id=cluster_id)


@router.get("/{cluster_id}/namespaces", response_model=list[NamespaceOut])
async def get_cluster_namespaces(
    cluster_id: str,
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List namespaces discovered in a cluster."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return [NamespaceOut.model_validate(ns) for ns in await service.get_namespaces(cluster_id)]


@router.get("/{cluster_id}/nodes", response_model=list[ClusterNodeOut])
async def get_cluster_nodes(
    cluster_id: str,
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List nodes discovered in a cluster."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return [ClusterNodeOut.model_validate(node) for node in await service.get_nodes(cluster_id)]


@router.get("/{cluster_id}/deployments", response_model=list[WorkloadOut])
async def get_cluster_deployments(
    cluster_id: str,
    namespace: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=200),
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List Kubernetes deployments discovered in a cluster."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    deployments = await service.get_deployments(cluster_id, namespace, skip, limit)
    return [WorkloadOut.model_validate(w) for w in deployments]


@router.get("/{cluster_id}/workloads", response_model=list[WorkloadOut])
async def get_cluster_workloads(
    cluster_id: str,
    namespace: str | None = Query(default=None),
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


@router.get("/{cluster_id}/pods", response_model=list[PodOut])
async def get_cluster_pods(
    cluster_id: str,
    namespace: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=500),
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List Kubernetes pods discovered in a cluster."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    pods = await service.get_pods(cluster_id, namespace, skip, limit)
    return [PodOut.model_validate(pod) for pod in pods]


@router.get("/{cluster_id}/services", response_model=list[ServiceOut])
async def get_cluster_services(
    cluster_id: str,
    namespace: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=500),
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List Kubernetes services discovered in a cluster."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    services = await service.get_services(cluster_id, namespace, skip, limit)
    return [ServiceOut.model_validate(svc) for svc in services]


@router.get("/{cluster_id}/replicasets", response_model=list[ReplicaSetOut])
async def get_cluster_replicasets(
    cluster_id: str,
    namespace: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=500),
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List Kubernetes ReplicaSets discovered in a cluster."""
    cluster = await service.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    replicasets = await service.get_replicasets(cluster_id, namespace, skip, limit)
    return [ReplicaSetOut.model_validate(rs) for rs in replicasets]


@router.get("/{cluster_id}/topology", response_model=ClusterTopologyOut)
async def get_cluster_topology(
    cluster_id: str,
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Return cluster → namespace → deployment → pod topology from persisted data."""
    topology = await service.get_topology(cluster_id)
    if not topology:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return ClusterTopologyOut.model_validate(topology)


@router.get("/{cluster_id}/summary")
async def get_cluster_summary(
    cluster_id: str,
    service: ClusterService = Depends(get_cluster_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get a high-level cluster health summary for the dashboard."""
    return await service.get_cluster_summary(cluster_id)
