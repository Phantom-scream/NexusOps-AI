"""Audit trail API."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, require_admin
from app.models.audit import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditEventListResponse, AuditEventOut

router = APIRouter()


def get_audit_repository(db: AsyncSession = Depends(get_db)) -> AuditRepository:
    return AuditRepository(model=AuditEvent, session=db)


@router.get("/events", response_model=AuditEventListResponse)
async def list_audit_events(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    actor_email: str | None = Query(default=None),
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    repository: AuditRepository = Depends(get_audit_repository),
    _: CurrentUser = Depends(require_admin),
):
    """List security and operations audit events."""
    skip = (page - 1) * page_size
    items = await repository.list_events(
        skip=skip,
        limit=page_size,
        actor_email=actor_email,
        action=action,
        resource_type=resource_type,
        status=status_filter,
    )
    total = await repository.count_events(
        actor_email=actor_email,
        action=action,
        resource_type=resource_type,
        status=status_filter,
    )
    return AuditEventListResponse(
        items=[AuditEventOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )
