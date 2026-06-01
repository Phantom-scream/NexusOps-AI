"""AI incident investigation domain models."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Investigation(Base, UUIDMixin, TimestampMixin):
    """A persisted AI investigation run for an incident or ad-hoc query."""

    __tablename__ = "investigations"

    incident_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cluster_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="created", index=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="medium", index=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    affected_resources: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    supporting_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    remediation_recommendations: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    investigation_context: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    context_sources: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)

    llm_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(150), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    evidence_items: Mapped[list["InvestigationEvidence"]] = relationship(
        "InvestigationEvidence",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )


class InvestigationEvidence(Base, UUIDMixin, TimestampMixin):
    """A normalized evidence item collected for an investigation."""

    __tablename__ = "investigation_evidence"

    investigation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="info", index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cluster_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    namespace_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deployment_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pod_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    service_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, default=dict)

    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="evidence_items")
