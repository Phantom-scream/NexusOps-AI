"""
NexusOps AI — Security Pydantic Schemas
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SecurityFindingOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    severity: str
    category: str
    status: str
    scanner: Optional[str]
    rule_id: Optional[str]
    cve_id: Optional[str]
    cluster_name: Optional[str]
    resource_type: Optional[str]
    resource_name: Optional[str]
    namespace: Optional[str]
    file_path: Optional[str]
    ai_explanation: Optional[str]
    remediation_suggestion: Optional[str]
    cvss_score: Optional[float]
    risk_score: Optional[float]
    is_acknowledged: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TerraformScanRequest(BaseModel):
    scan_name: str = Field(..., min_length=3, max_length=255)
    repository_url: Optional[str] = None
    branch: Optional[str] = "main"
    scan_path: Optional[str] = None
    terraform_content: Optional[str] = None


class TerraformScanOut(BaseModel):
    id: str
    scan_name: str
    repository_url: Optional[str]
    branch: Optional[str]
    status: str
    findings_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    drift_detected: bool
    ai_summary: Optional[str]
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
    findings_by_category: Dict[str, int]
    top_clusters: List[Dict[str, Any]]
    recent_findings: List[SecurityFindingOut]


class SecurityFindingListResponse(BaseModel):
    items: List[SecurityFindingOut]
    total: int
    page: int
    page_size: int
