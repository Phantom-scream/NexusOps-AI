"""AI investigation API."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user, require_operator
from app.models.audit import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationEvidenceOut,
    InvestigationListResponse,
    InvestigationOut,
    InvestigationRunResponse,
)
from app.services.audit_service import AuditService
from app.services.investigation_service import InvestigationService

router = APIRouter()


def get_investigation_service(db: AsyncSession = Depends(get_db)) -> InvestigationService:
    return InvestigationService.from_session(db)


@router.post("/investigations", response_model=InvestigationOut, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    data: InvestigationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: InvestigationService = Depends(get_investigation_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Create an investigation and optionally run it immediately."""
    investigation = await service.create_investigation(data)
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="investigation.create",
        actor=current_user,
        request=request,
        resource_type="investigation",
        resource_id=investigation.id,
        metadata={"incident_id": investigation.incident_id, "run_immediately": data.run_immediately},
    )
    return InvestigationOut.model_validate(investigation)


@router.get("/investigations", response_model=InvestigationListResponse)
async def list_investigations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    incident_id: str | None = Query(default=None),
    cluster_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    service: InvestigationService = Depends(get_investigation_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List investigation history."""
    skip = (page - 1) * page_size
    items, total = await service.list_investigations(
        skip=skip,
        limit=page_size,
        incident_id=incident_id,
        cluster_id=cluster_id,
        status=status_filter,
    )
    return InvestigationListResponse(
        items=[InvestigationOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/investigations/{investigation_id}", response_model=InvestigationOut)
async def get_investigation(
    investigation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get one investigation result."""
    investigation = await service.get_investigation(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return InvestigationOut.model_validate(investigation)


@router.post("/investigations/{investigation_id}/run", response_model=InvestigationRunResponse)
async def run_investigation(
    investigation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: InvestigationService = Depends(get_investigation_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Run or rerun an investigation workflow."""
    try:
        investigation = await service.run_investigation(investigation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Investigation not found") from exc
    evidence = await service.get_evidence(investigation_id)
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="investigation.run",
        actor=current_user,
        request=request,
        resource_type="investigation",
        resource_id=investigation.id,
        metadata={"evidence": len(evidence), "confidence": investigation.confidence_score},
    )
    return InvestigationRunResponse(
        investigation=InvestigationOut.model_validate(investigation),
        evidence=[InvestigationEvidenceOut.model_validate(item) for item in evidence],
    )


@router.get("/investigations/{investigation_id}/evidence", response_model=list[InvestigationEvidenceOut])
async def get_investigation_evidence(
    investigation_id: str,
    service: InvestigationService = Depends(get_investigation_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Return normalized evidence collected for an investigation."""
    investigation = await service.get_investigation(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return [InvestigationEvidenceOut.model_validate(item) for item in await service.get_evidence(investigation_id)]
