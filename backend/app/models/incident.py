"""
NexusOps AI — Incident Models
"""
from enum import Enum

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class IncidentSource(str, Enum):
    KUBERNETES = "kubernetes"
    PROMETHEUS = "prometheus"
    LOKI = "loki"
    MANUAL = "manual"
    AI_DETECTED = "ai_detected"
    TERRAFORM = "terraform"


class Incident(Base, UUIDMixin, TimestampMixin):
    """Represents a detected infrastructure incident."""
    __tablename__ = "incidents"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default=IncidentSeverity.MEDIUM, index=True)
    status: Mapped[str] = mapped_column(String(30), default=IncidentStatus.OPEN, index=True)
    source: Mapped[str] = mapped_column(String(30), default=IncidentSource.KUBERNETES)

    # Affected resources
    cluster_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(255), nullable=True)
    affected_workload: Mapped[str | None] = mapped_column(String(255), nullable=True)
    affected_resources: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)

    # AI Analysis
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    contributing_factors: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_analysis_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Remediation
    remediation_steps: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    remediation_applied: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    raw_events: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    alert_count: Mapped[int] = mapped_column(Integer, default=1)
    assignee: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    analyses: Mapped[list["IncidentAnalysis"]] = relationship("IncidentAnalysis", back_populates="incident", cascade="all, delete-orphan")


class IncidentAnalysis(Base, UUIDMixin, TimestampMixin):
    """AI analysis result for an incident."""
    __tablename__ = "incident_analyses"

    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation_yaml: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    context_sources: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="analyses")
