"""Cost optimization and resource intelligence API."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user, require_operator
from app.models.audit import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.schemas.optimization import (
    CostRecommendationListResponse,
    CostRecommendationOut,
    OptimizationAnalysisResponse,
    OptimizationAnalyzeRequest,
    OptimizationDashboardStats,
    OptimizationFindingListResponse,
    OptimizationFindingOut,
    OptimizationReportListResponse,
    OptimizationReportOut,
    ResourceUtilizationOut,
)
from app.services.audit_service import AuditService
from app.services.optimization_service import OptimizationService

router = APIRouter()


def get_optimization_service(db: AsyncSession = Depends(get_db)) -> OptimizationService:
    return OptimizationService.from_session(db)


@router.post("/analyze", response_model=OptimizationAnalysisResponse)
async def analyze_optimization(
    request: OptimizationAnalyzeRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    service: OptimizationService = Depends(get_optimization_service),
    current_user: CurrentUser = Depends(require_operator),
):
    """Run cost optimization analysis over infrastructure and telemetry."""
    try:
        report, findings, recommendations, utilization, stats = await service.analyze(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="optimization.analyze",
        actor=current_user,
        request=http_request,
        resource_type="optimization_report",
        resource_id=report.id,
        metadata={
            "findings": len(findings),
            "recommendations": len(recommendations),
            "estimated_monthly_savings_usd": report.estimated_monthly_savings_usd,
        },
    )
    return OptimizationAnalysisResponse(
        report=OptimizationReportOut.model_validate(report),
        findings=[OptimizationFindingOut.model_validate(item) for item in findings],
        recommendations=[CostRecommendationOut.model_validate(item) for item in recommendations],
        utilization=[ResourceUtilizationOut.model_validate(item) for item in utilization],
        stats=stats,
    )


@router.get("/findings", response_model=OptimizationFindingListResponse)
async def list_findings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    cluster_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    finding_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    service: OptimizationService = Depends(get_optimization_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List optimization findings."""
    skip = (page - 1) * page_size
    items = await service.finding_repo.list_findings(
        skip=skip,
        limit=page_size,
        cluster_id=cluster_id,
        severity=severity,
        finding_type=finding_type,
        status=status_filter,
    )
    total = await service.finding_repo.count_findings(
        cluster_id=cluster_id,
        severity=severity,
        finding_type=finding_type,
        status=status_filter,
    )
    return OptimizationFindingListResponse(
        items=[OptimizationFindingOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/recommendations", response_model=CostRecommendationListResponse)
async def list_recommendations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    cluster_id: str | None = Query(default=None),
    optimization_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    service: OptimizationService = Depends(get_optimization_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List optimization recommendations."""
    skip = (page - 1) * page_size
    items = await service.recommendation_repo.list_recommendations(
        skip=skip,
        limit=page_size,
        cluster_id=cluster_id,
        optimization_type=optimization_type,
        severity=severity,
        status=status_filter,
    )
    total = await service.recommendation_repo.count_recommendations(
        cluster_id=cluster_id,
        optimization_type=optimization_type,
        severity=severity,
        status=status_filter,
    )
    return CostRecommendationListResponse(
        items=[CostRecommendationOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/recommendations/{recommendation_id}", response_model=CostRecommendationOut)
async def get_recommendation(
    recommendation_id: str,
    service: OptimizationService = Depends(get_optimization_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get one optimization recommendation."""
    recommendation = await service.recommendation_repo.get(recommendation_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="Optimization recommendation not found")
    return CostRecommendationOut.model_validate(recommendation)


@router.get("/reports", response_model=OptimizationReportListResponse)
async def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: OptimizationService = Depends(get_optimization_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List optimization report history."""
    skip = (page - 1) * page_size
    items = await service.report_repo.get_all(skip=skip, limit=page_size)
    total = await service.report_repo.count()
    return OptimizationReportListResponse(
        items=[OptimizationReportOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=OptimizationDashboardStats)
async def get_stats(
    service: OptimizationService = Depends(get_optimization_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get optimization dashboard statistics."""
    return await service.stats()
