"""Audit trail service."""

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import Request

from app.core.security import CurrentUser
from app.models.audit import AuditEvent
from app.repositories.audit_repository import AuditRepository

logger = structlog.get_logger(__name__)


class AuditService:
    """Records security and operations audit events."""

    def __init__(self, repository: AuditRepository):
        self.repository = repository

    async def record(
        self,
        *,
        action: str,
        actor: CurrentUser | None = None,
        request: Request | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        status: str = "success",
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent | None:
        event = AuditEvent(
            actor_id=actor.user_id if actor else None,
            actor_email=actor.email if actor else None,
            actor_role=actor.role if actor else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            request_id=getattr(request.state, "request_id", None) if request else None,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            timestamp=datetime.now(UTC),
            metadata_=metadata or {},
        )
        try:
            return await self.repository.create(event)
        except Exception as exc:
            logger.warning("Audit event write failed", action=action, error=str(exc))
            return None
