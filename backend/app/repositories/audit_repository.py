"""Repository for audit event persistence and retrieval."""

from collections.abc import Sequence

from sqlalchemy import func, select

from app.models.audit import AuditEvent
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditEvent]):
    """Data access helpers for immutable audit events."""

    async def list_events(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        actor_email: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
    ) -> Sequence[AuditEvent]:
        stmt = select(AuditEvent)
        stmt = self._apply_filters(
            stmt,
            actor_email=actor_email,
            action=action,
            resource_type=resource_type,
            status=status,
        )
        stmt = stmt.order_by(AuditEvent.timestamp.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_events(
        self,
        *,
        actor_email: str | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        status: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(AuditEvent)
        stmt = self._apply_filters(
            stmt,
            actor_email=actor_email,
            action=action,
            resource_type=resource_type,
            status=status,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def _apply_filters(
        self,
        stmt,
        *,
        actor_email: str | None,
        action: str | None,
        resource_type: str | None,
        status: str | None,
    ):
        if actor_email:
            stmt = stmt.where(AuditEvent.actor_email == actor_email)
        if action:
            stmt = stmt.where(AuditEvent.action == action)
        if resource_type:
            stmt = stmt.where(AuditEvent.resource_type == resource_type)
        if status:
            stmt = stmt.where(AuditEvent.status == status)
        return stmt
