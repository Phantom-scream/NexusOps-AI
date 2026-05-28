"""
NexusOps AI — Cost Optimization Models
"""
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
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

    cluster_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    namespace: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    workload_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    workload_kind: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    optimization_type: Mapped[str] = mapped_column(String(50), default=OptimizationType.RIGHT_SIZING, index=True)
    status: Mapped[str] = mapped_column(String(30), default=OptimizationStatus.OPEN, index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Current state
    current_cpu_request_millicores: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_memory_request_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_cpu_usage_avg_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_memory_usage_avg_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_replicas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Recommended state
    recommended_cpu_request_millicores: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recommended_memory_request_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recommended_replicas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Savings
    estimated_monthly_savings_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_cpu_savings_cores: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_memory_savings_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    ai_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_yaml: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)


class CostAnalysisReport(Base, UUIDMixin, TimestampMixin):
    """Periodic cost analysis report for a cluster."""
    __tablename__ = "cost_analysis_reports"

    cluster_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    total_monthly_cost_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    potential_savings_usd: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    optimization_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    overprovisioned_workloads: Mapped[int] = mapped_column(Integer, default=0)
    idle_workloads: Mapped[int] = mapped_column(Integer, default=0)
    total_recommendations: Mapped[int] = mapped_column(Integer, default=0)

    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
