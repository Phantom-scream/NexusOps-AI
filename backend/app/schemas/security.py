"""
NexusOps AI — Security Pydantic Schemas
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SecurityFindingOut(BaseModel):
    id: str
    title: str
    description: str | None
    severity: str
    category: str
    status: str
    scanner: str | None
    rule_id: str | None
    cve_id: str | None
    cluster_name: str | None
    resource_type: str | None
    resource_name: str | None
    namespace: str | None
    file_path: str | None
    ai_explanation: str | None
    remediation_suggestion: str | None
    cvss_score: float | None
    risk_score: float | None
    is_acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TerraformScanRequest(BaseModel):
    scan_name: str = Field(..., min_length=3, max_length=255)
    repository_url: str | None = None
    branch: str | None = "main"
    scan_path: str | None = None
    terraform_content: str | None = None


class TerraformScanOut(BaseModel):
    id: str
    scan_name: str
    repository_url: str | None
    branch: str | None
    status: str
    findings_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    drift_detected: bool
    ai_summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SecurityDashboardStats(BaseModel):
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    open_findings: int
    remediated_findings: int
    findings_by_category: dict[str, int]
    top_clusters: list[dict[str, Any]]
    recent_findings: list[SecurityFindingOut]


class SecurityFindingListResponse(BaseModel):
    items: list[SecurityFindingOut]
    total: int
    page: int
    page_size: int
