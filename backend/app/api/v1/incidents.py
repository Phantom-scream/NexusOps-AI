"""
NexusOps AI — Incidents API
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user, require_operator
from app.models.audit import AuditEvent
from app.models.incident import Incident, IncidentAnalysis
from app.repositories.audit_repository import AuditRepository
from app.repositories.incident_repository import IncidentAnalysisRepository, IncidentRepository
from app.schemas.incident import (
    IncidentAnalysisOut,
    IncidentCreate,
    IncidentListResponse,
    IncidentOut,
    IncidentUpdate,
)
from app.services.audit_service import AuditService
from app.services.incident_service import IncidentService

router = APIRouter()


def get_incident_service(db: AsyncSession = Depends(get_db)) -> IncidentService:
    return IncidentService(
        repository=IncidentRepository(model=Incident, session=db),
        analysis_repository=IncidentAnalysisRepository(model=IncidentAnalysis, session=db),
    )


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None, alias="status"),
    cluster_id: str | None = Query(default=None),
    service: IncidentService = Depends(get_incident_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List incidents with optional filters."""
    skip = (page - 1) * page_size
    incidents, total = await service.list_incidents(
        skip=skip, limit=page_size,
        severity=severity, status=status, cluster_id=cluster_id,
    )
    return IncidentListResponse(
        items=[IncidentOut.model_validate(i) for i in incidents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Manually create an incident."""
    incident = await service.create_incident(data)
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="incident.create",
        actor=current_user,
        request=request,
        resource_type="incident",
        resource_id=incident.id,
        metadata={"severity": incident.severity, "cluster_id": incident.cluster_id},
    )
    return IncidentOut.model_validate(incident)


@router.get("/stats")
async def get_incident_stats(
    service: IncidentService = Depends(get_incident_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get incident dashboard statistics."""
    return await service.get_dashboard_stats()


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(
    incident_id: str,
    service: IncidentService = Depends(get_incident_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get incident details."""
    incident = await service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentOut.model_validate(incident)


@router.patch("/{incident_id}", response_model=IncidentOut)
async def update_incident(
    incident_id: str,
    data: IncidentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Update incident metadata or status."""
    incident = await service.update_incident(incident_id, data)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="incident.update",
        actor=current_user,
        request=request,
        resource_type="incident",
        resource_id=incident.id,
        metadata=data.model_dump(exclude_unset=True),
    )
    return IncidentOut.model_validate(incident)


@router.post("/{incident_id}/resolve", response_model=IncidentOut)
async def resolve_incident(
    incident_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Mark an incident as resolved."""
    incident = await service.resolve_incident(incident_id, resolved_by=current_user.email)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="incident.resolve",
        actor=current_user,
        request=request,
        resource_type="incident",
        resource_id=incident.id,
        metadata={"resolved_by": current_user.email},
    )
    return IncidentOut.model_validate(incident)


@router.post("/{incident_id}/investigate", status_code=status.HTTP_202_ACCEPTED)
async def trigger_ai_investigation(
    incident_id: str,
    request: Request,
    query: str = Query(..., min_length=10),
    context_window_minutes: int = Query(default=60, ge=5, le=1440),
    db: AsyncSession = Depends(get_db),
    service: IncidentService = Depends(get_incident_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Trigger asynchronous AI investigation for an incident."""
    incident = await service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    from app.workers.analysis_tasks import analyze_incident_task
    task = analyze_incident_task.delay(incident_id, query, context_window_minutes)

    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="incident.investigate",
        actor=current_user,
        request=request,
        resource_type="incident",
        resource_id=incident_id,
        metadata={"task_id": task.id, "context_window_minutes": context_window_minutes},
    )
    return {"task_id": task.id, "status": "queued", "incident_id": incident_id}


@router.get("/{incident_id}/analyses", response_model=list[IncidentAnalysisOut])
async def get_incident_analyses(
    incident_id: str,
    service: IncidentService = Depends(get_incident_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get all AI analyses for an incident."""
    incident = await service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return [IncidentAnalysisOut.model_validate(a) for a in incident.analyses]
