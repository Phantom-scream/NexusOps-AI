"""Telemetry domain models for infrastructure observability."""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class TelemetrySource(Base, UUIDMixin, TimestampMixin):
    """A telemetry producer such as demo generation, Prometheus, Loki, or OTEL."""

    __tablename__ = "telemetry_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    endpoint_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cluster_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)


class Metric(Base, UUIDMixin, TimestampMixin):
    """Historical numeric telemetry linked to infrastructure resources."""

    __tablename__ = "metrics"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="count")
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, default="cluster", index=True)
    resource_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("telemetry_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cluster_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    namespace_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    deployment_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    pod_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    service_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )

    labels: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)


class LogEntry(Base, UUIDMixin, TimestampMixin):
    """Centralized log entry with infrastructure and trace correlation fields."""

    __tablename__ = "log_entries"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="info", index=True)
    source: Mapped[str] = mapped_column(String(150), nullable=False, default="application")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("telemetry_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cluster_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    namespace_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    deployment_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    pod_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    service_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trace_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    span_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)


class InfrastructureEvent(Base, UUIDMixin, TimestampMixin):
    """Kubernetes and platform events normalized for investigation."""

    __tablename__ = "infrastructure_events"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(150), nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="info", index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("telemetry_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cluster_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    namespace_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    deployment_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    pod_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    service_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)


class Trace(Base, UUIDMixin, TimestampMixin):
    """OpenTelemetry-compatible trace span persisted for topology correlation."""

    __tablename__ = "traces"

    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    span_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parent_span_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    operation_name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ok", index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    source_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("telemetry_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cluster_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    namespace_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    deployment_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    pod_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
