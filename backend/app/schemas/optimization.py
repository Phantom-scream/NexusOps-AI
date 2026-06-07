"""Cost optimization and resource intelligence schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class OptimizationAnalyzeRequest(BaseModel):
    cluster_id: str | None = None
    demo: bool = False
    analysis_window_hours: int = 24
    report_name: str | None = None


class ResourceUtilizationOut(BaseModel):
    id: str
    cluster_id: str | None
    cluster_name: str | None
    namespace: str | None
    resource_type: str
    resource_name: str
    workload_kind: str | None
    cpu_request_millicores: int | None
    memory_request_mb: int | None
    cpu_limit_millicores: int | None
    memory_limit_mb: int | None
    cpu_usage_avg_percent: float | None
    memory_usage_avg_percent: float | None
    cpu_usage_p95_percent: float | None
    memory_usage_p95_percent: float | None
    request_count_avg: float | None
    error_rate_avg_percent: float | None
    restart_count: int
    replicas_desired: int | None
    replicas_ready: int | None
    sample_count: int
    observation_window_hours: int
    monthly_cost_estimate_usd: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OptimizationRuleOut(BaseModel):
    id: str
    name: str
    rule_type: str
    description: str
    severity: str
    is_enabled: bool
    parameters: dict[str, Any] | None

    model_config = {"from_attributes": True}


class OptimizationFindingOut(BaseModel):
    id: str
    report_id: str | None
    rule_id: str | None
    utilization_id: str | None
    cluster_id: str | None
    cluster_name: str | None
    namespace: str | None
    resource_type: str
    resource_name: str
    finding_type: str
    severity: str
    title: str
    description: str
    evidence: dict[str, Any] | None
    confidence_score: float | None
    estimated_monthly_savings_usd: float | None
    recommendation: str | None
    remediation: str | None
    ai_explanation: str | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CostRecommendationOut(BaseModel):
    id: str
    report_id: str | None
    finding_id: str | None
    cluster_id: str | None
    cluster_name: str | None
    namespace: str | None
    workload_name: str | None
    workload_kind: str | None
    resource_type: str | None
    resource_name: str | None
    optimization_type: str
    status: str
    severity: str
    confidence_score: float | None
    title: str
    description: str | None
    recommendation: str | None
    impact: str | None
    current_cpu_request_millicores: int | None
    current_memory_request_mb: int | None
    current_cpu_usage_avg_percent: float | None
    current_memory_usage_avg_percent: float | None
    current_replicas: int | None
    recommended_cpu_request_millicores: int | None
    recommended_memory_request_mb: int | None
    recommended_replicas: int | None
    estimated_monthly_savings_usd: float | None
    estimated_cpu_savings_cores: float | None
    estimated_memory_savings_gb: float | None
    ai_explanation: str | None
    remediation_yaml: str | None
    evidence: dict[str, Any] | None
    priority: int
    created_at: datetime

    model_config = {"from_attributes": True}


class OptimizationReportOut(BaseModel):
    id: str
    report_name: str
    cluster_id: str | None
    cluster_name: str | None
    status: str
    analysis_window_hours: int
    total_resources_analyzed: int
    total_findings: int
    total_recommendations: int
    estimated_monthly_savings_usd: float
    estimated_annual_savings_usd: float
    optimization_score: float | None
    summary: str | None
    severity_breakdown: dict[str, int] | None
    category_breakdown: dict[str, int] | None
    impacted_resources: list[dict[str, Any]] | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class OptimizationDashboardStats(BaseModel):
    total_recommendations: int
    open_recommendations: int
    implemented_recommendations: int
    in_progress_recommendations: int
    total_findings: int
    critical_findings: int
    high_findings: int
    estimated_monthly_savings_usd: float
    estimated_annual_savings_usd: float
    optimization_score: float
    severity_breakdown: dict[str, int]
    type_breakdown: dict[str, int]
    top_recommendations: list[CostRecommendationOut]


class OptimizationFindingListResponse(BaseModel):
    items: list[OptimizationFindingOut]
    total: int
    page: int
    page_size: int


class CostRecommendationListResponse(BaseModel):
    items: list[CostRecommendationOut]
    total: int
    page: int
    page_size: int


class OptimizationReportListResponse(BaseModel):
    items: list[OptimizationReportOut]
    total: int
    page: int
    page_size: int


class OptimizationAnalysisResponse(BaseModel):
    report: OptimizationReportOut
    findings: list[OptimizationFindingOut]
    recommendations: list[CostRecommendationOut]
    utilization: list[ResourceUtilizationOut]
    stats: OptimizationDashboardStats
