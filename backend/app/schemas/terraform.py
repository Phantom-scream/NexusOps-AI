"""Terraform security and drift schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TerraformWorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = None
    source_type: str = "upload"
    repository_url: str | None = None
    branch: str | None = "main"
    root_path: str | None = None
    provider: str | None = None
    environment: str | None = None
    owner: str | None = None
    metadata: dict[str, Any] | None = None


class TerraformUploadRequest(TerraformWorkspaceCreate):
    files: dict[str, str] | None = None
    terraform_content: str | None = None
    state: dict[str, Any] | None = None


class TerraformAnalyzeRequest(BaseModel):
    workspace_id: str | None = None
    workspace_name: str | None = None
    files: dict[str, str] | None = None
    terraform_content: str | None = None
    state: dict[str, Any] | None = None
    demo: bool = False
    scan_name: str | None = None


class TerraformWorkspaceOut(BaseModel):
    id: str
    name: str
    description: str | None
    source_type: str
    repository_url: str | None
    branch: str | None
    root_path: str | None
    provider: str | None
    environment: str | None
    owner: str | None
    last_scan_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TerraformResourceOut(BaseModel):
    id: str
    workspace_id: str
    scan_id: str | None
    address: str
    type: str
    name: str
    provider: str | None
    module: str | None
    file_path: str | None
    line_number: int | None
    desired_config: dict[str, Any] | None
    actual_state: dict[str, Any] | None
    drift_status: str
    risk_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TerraformFindingOut(BaseModel):
    id: str
    workspace_id: str
    scan_id: str | None
    resource_id: str | None
    title: str
    description: str
    impact: str | None
    severity: str
    category: str
    status: str
    scanner: str
    rule_id: str | None
    resource_address: str | None
    resource_type: str | None
    file_path: str | None
    line_number: int | None
    remediation: str | None
    ai_explanation: str | None
    confidence_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TerraformDriftOut(BaseModel):
    id: str
    workspace_id: str
    scan_id: str | None
    resource_id: str | None
    resource_address: str
    resource_type: str | None
    attribute_path: str
    desired_value: Any | None
    actual_value: Any | None
    drift_type: str
    severity: str
    status: str
    description: str
    remediation: str | None
    confidence_score: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TerraformPolicyViolationOut(BaseModel):
    id: str
    workspace_id: str
    scan_id: str | None
    finding_id: str | None
    policy_name: str
    rule_id: str | None
    message: str
    severity: str
    resource_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TerraformScanOut(BaseModel):
    id: str
    workspace_id: str | None
    scan_name: str
    source_type: str
    repository_url: str | None
    branch: str | None
    scan_path: str | None
    status: str
    findings_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    policy_violation_count: int
    drift_count: int
    drift_detected: bool
    ai_summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TerraformDashboardStats(BaseModel):
    total_workspaces: int
    total_resources: int
    total_findings: int
    open_findings: int
    critical_findings: int
    high_findings: int
    drift_count: int
    policy_violation_count: int
    severity_breakdown: dict[str, int]
    category_breakdown: dict[str, int]


class TerraformFindingListResponse(BaseModel):
    items: list[TerraformFindingOut]
    total: int
    page: int
    page_size: int


class TerraformDriftListResponse(BaseModel):
    items: list[TerraformDriftOut]
    total: int
    page: int
    page_size: int


class TerraformAnalysisResponse(BaseModel):
    workspace: TerraformWorkspaceOut
    scan: TerraformScanOut
    resources: list[TerraformResourceOut]
    findings: list[TerraformFindingOut]
    drift: list[TerraformDriftOut]
    policy_violations: list[TerraformPolicyViolationOut]
    stats: TerraformDashboardStats
