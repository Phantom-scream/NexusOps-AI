"""
NexusOps AI — Security Finding Models
"""
from enum import Enum

from sqlalchemy import JSON, Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingCategory(str, Enum):
    IAM = "iam"
    NETWORK = "network"
    ENCRYPTION = "encryption"
    RBAC = "rbac"
    SECRETS = "secrets"
    DOCKERFILE = "dockerfile"
    TERRAFORM = "terraform"
    KUBERNETES = "kubernetes"
    COMPLIANCE = "compliance"
    VULNERABILITY = "vulnerability"


class FindingStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    REMEDIATED = "remediated"
    SUPPRESSED = "suppressed"
    FALSE_POSITIVE = "false_positive"


class SecurityFinding(Base, UUIDMixin, TimestampMixin):
    """Represents a security finding from Trivy, OPA, or AI analysis."""
    __tablename__ = "security_findings"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default=FindingSeverity.MEDIUM, index=True)
    category: Mapped[str] = mapped_column(String(50), default=FindingCategory.KUBERNETES, index=True)
    status: Mapped[str] = mapped_column(String(30), default=FindingStatus.OPEN, index=True)

    # Source
    scanner: Mapped[str | None] = mapped_column(String(100), nullable=True)  # trivy, opa, ai
    rule_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cve_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Affected Resource
    cluster_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True, index=True)
    cluster_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    namespace: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Details
    raw_finding: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation_code: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Risk scoring
    cvss_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TerraformScan(Base, UUIDMixin, TimestampMixin):
    """Represents a Terraform security scan session."""
    __tablename__ = "terraform_scans"

    workspace_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("terraform_workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    scan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="upload")
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scan_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")

    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    critical_count: Mapped[int] = mapped_column(Integer, default=0)
    high_count: Mapped[int] = mapped_column(Integer, default=0)
    medium_count: Mapped[int] = mapped_column(Integer, default=0)
    low_count: Mapped[int] = mapped_column(Integer, default=0)

    policy_violation_count: Mapped[int] = mapped_column(Integer, default=0)
    drift_count: Mapped[int] = mapped_column(Integer, default=0)
    drift_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    drift_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    scan_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
