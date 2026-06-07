"""Terraform security and drift domain models."""

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class TerraformWorkspace(Base, UUIDMixin, TimestampMixin):
    """Logical Terraform project or environment analyzed by NexusOps."""

    __tablename__ = "terraform_workspaces"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="upload", index=True)
    repository_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    root_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    environment: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_scan_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, default=dict)

    resources: Mapped[list["TerraformResource"]] = relationship(
        "TerraformResource",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    findings: Mapped[list["TerraformFinding"]] = relationship(
        "TerraformFinding",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    drift_records: Mapped[list["TerraformDrift"]] = relationship(
        "TerraformDrift",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    policy_violations: Mapped[list["TerraformPolicyViolation"]] = relationship(
        "TerraformPolicyViolation",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )


class TerraformResource(Base, UUIDMixin, TimestampMixin):
    """Parsed Terraform resource with desired and optional actual state."""

    __tablename__ = "terraform_resources"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("terraform_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("terraform_scans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    address: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    module: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    desired_config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    actual_state: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    drift_status: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown", index=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    workspace: Mapped["TerraformWorkspace"] = relationship("TerraformWorkspace", back_populates="resources")


class TerraformFinding(Base, UUIDMixin, TimestampMixin):
    """IaC security, compliance, or policy finding from Terraform analysis."""

    __tablename__ = "terraform_findings"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("terraform_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("terraform_scans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("terraform_resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="medium", index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False, default="terraform", index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)
    scanner: Mapped[str] = mapped_column(String(100), nullable=False, default="nexusops")
    rule_id: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    resource_address: Mapped[str | None] = mapped_column(String(500), nullable=True, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_finding: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    workspace: Mapped["TerraformWorkspace"] = relationship("TerraformWorkspace", back_populates="findings")


class TerraformDrift(Base, UUIDMixin, TimestampMixin):
    """Difference between Terraform desired state and ingested actual state."""

    __tablename__ = "terraform_drift"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("terraform_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("terraform_scans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("terraform_resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resource_address: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(150), nullable=True)
    attribute_path: Mapped[str] = mapped_column(String(500), nullable=False)
    desired_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSON, nullable=True)
    actual_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSON, nullable=True)
    drift_type: Mapped[str] = mapped_column(String(50), nullable=False, default="changed", index=True)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="medium", index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    workspace: Mapped["TerraformWorkspace"] = relationship("TerraformWorkspace", back_populates="drift_records")


class TerraformPolicyViolation(Base, UUIDMixin, TimestampMixin):
    """OPA or policy-framework violation produced during analysis."""

    __tablename__ = "terraform_policy_violations"

    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("terraform_workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("terraform_scans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    finding_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("terraform_findings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False, default="nexusops.terraform.security")
    rule_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(30), nullable=False, default="medium", index=True)
    resource_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    input_document: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    opa_result: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    workspace: Mapped["TerraformWorkspace"] = relationship("TerraformWorkspace", back_populates="policy_violations")
    finding: Mapped["TerraformFinding"] = relationship("TerraformFinding")
