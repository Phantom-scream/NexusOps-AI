"""
NexusOps AI — Cost Optimization Models
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class OptimizationType(str, Enum):
    RIGHT_SIZING = "right_sizing"
    IDLE_REMOVAL = "idle_removal"
    AUTOSCALING = "autoscaling"
    SPOT_MIGRATION = "spot_migration"
    RESERVED_INSTANCES = "reserved_instances"
    STORAGE_OPTIMIZATION = "storage_optimization"


class OptimizationStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    DISMISSED = "dismissed"


class CostRecommendation(Base, UUIDMixin, TimestampMixin):
    """Represents a cost optimization recommendation."""
    __tablename__ = "cost_recommendations"

    report_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("optimization_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    finding_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("optimization_findings.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workload_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workload_kind: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    optimization_type: Mapped[str] = mapped_column(String(50), default=OptimizationType.RIGHT_SIZING, index=True)
    status: Mapped[str] = mapped_column(String(30), default=OptimizationStatus.OPEN, index=True)
    severity: Mapped[str] = mapped_column(String(30), default="medium", index=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Current state
    current_cpu_request_millicores: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_memory_request_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_cpu_usage_avg_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_memory_usage_avg_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_replicas: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Recommended state
    recommended_cpu_request_millicores: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_memory_request_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_replicas: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Savings
    estimated_monthly_savings_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_cpu_savings_cores: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_memory_savings_gb: Mapped[float | None] = mapped_column(Float, nullable=True)

    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation_yaml: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=5)


class CostAnalysisReport(Base, UUIDMixin, TimestampMixin):
    """Periodic cost analysis report for a cluster."""
    __tablename__ = "cost_analysis_reports"

    cluster_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    total_monthly_cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    potential_savings_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    optimization_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    overprovisioned_workloads: Mapped[int] = mapped_column(Integer, default=0)
    idle_workloads: Mapped[int] = mapped_column(Integer, default=0)
    total_recommendations: Mapped[int] = mapped_column(Integer, default=0)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ResourceUtilization(Base, UUIDMixin, TimestampMixin):
    """Normalized utilization snapshot for a cluster resource."""

    __tablename__ = "resource_utilization"

    cluster_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    workload_kind: Mapped[str | None] = mapped_column(String(50), nullable=True)

    cpu_request_millicores: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_request_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpu_limit_millicores: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_limit_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cpu_usage_avg_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_usage_avg_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    cpu_usage_p95_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_usage_p95_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    request_count_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_rate_avg_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    restart_count: Mapped[int] = mapped_column(Integer, default=0)
    replicas_desired: Mapped[int | None] = mapped_column(Integer, nullable=True)
    replicas_ready: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    observation_window_hours: Mapped[int] = mapped_column(Integer, default=24)
    monthly_cost_estimate_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, default=dict)


class OptimizationRule(Base, UUIDMixin, TimestampMixin):
    """Deterministic optimization rule metadata."""

    __tablename__ = "optimization_rules"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    rule_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(30), default="medium", index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)


class OptimizationReport(Base, UUIDMixin, TimestampMixin):
    """A persisted optimization report across clusters or one cluster."""

    __tablename__ = "optimization_reports"

    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cluster_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="completed", index=True)
    analysis_window_hours: Mapped[int] = mapped_column(Integer, default=24)
    total_resources_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    total_recommendations: Mapped[int] = mapped_column(Integer, default=0)
    estimated_monthly_savings_usd: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_annual_savings_usd: Mapped[float] = mapped_column(Float, default=0.0)
    optimization_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    category_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    impacted_resources: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OptimizationFinding(Base, UUIDMixin, TimestampMixin):
    """Resource intelligence finding produced by optimization rules."""

    __tablename__ = "optimization_findings"

    report_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("optimization_reports.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("optimization_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    utilization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("resource_utilization.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    finding_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="medium", index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_monthly_savings_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)
