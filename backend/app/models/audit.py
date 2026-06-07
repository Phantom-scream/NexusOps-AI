"""Audit trail domain model."""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class AuditEvent(Base, UUIDMixin, TimestampMixin):
    """Immutable security and operations audit event."""

    __tablename__ = "audit_events"

    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    actor_email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    actor_role: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="success", index=True)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        index=True,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, default=dict)
