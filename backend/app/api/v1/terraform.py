"""Terraform security and drift API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user
from app.schemas.terraform import (
    TerraformAnalysisResponse,
    TerraformAnalyzeRequest,
    TerraformDashboardStats,
    TerraformDriftListResponse,
    TerraformDriftOut,
    TerraformFindingListResponse,
    TerraformFindingOut,
    TerraformPolicyViolationOut,
    TerraformResourceOut,
    TerraformScanOut,
    TerraformUploadRequest,
    TerraformWorkspaceOut,
)
from app.services.terraform_service import TerraformAnalysisService

router = APIRouter()


def get_terraform_service(db: AsyncSession = Depends(get_db)) -> TerraformAnalysisService:
    return TerraformAnalysisService.from_session(db)


@router.post("/upload", response_model=TerraformWorkspaceOut, status_code=status.HTTP_201_CREATED)
async def upload_terraform_directory(
    request: TerraformUploadRequest,
    service: TerraformAnalysisService = Depends(get_terraform_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Ingest Terraform files into a workspace without running analysis."""
    try:
        workspace, _ = await service.upload(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TerraformWorkspaceOut.model_validate(workspace)


@router.post("/analyze", response_model=TerraformAnalysisResponse)
async def analyze_terraform(
    request: TerraformAnalyzeRequest,
    service: TerraformAnalysisService = Depends(get_terraform_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Analyze Terraform for security findings, policy violations, and drift."""
    try:
        workspace, scan, resources, findings, drift, policy_violations, stats = await service.analyze(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TerraformAnalysisResponse(
        workspace=TerraformWorkspaceOut.model_validate(workspace),
        scan=TerraformScanOut.model_validate(scan),
        resources=[TerraformResourceOut.model_validate(item) for item in resources],
        findings=[TerraformFindingOut.model_validate(item) for item in findings],
        drift=[TerraformDriftOut.model_validate(item) for item in drift],
        policy_violations=[TerraformPolicyViolationOut.model_validate(item) for item in policy_violations],
        stats=stats,
    )


@router.get("/workspaces", response_model=list[TerraformWorkspaceOut])
async def list_workspaces(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: TerraformAnalysisService = Depends(get_terraform_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List Terraform workspaces."""
    items = await service.workspace_repo.get_all(skip=(page - 1) * page_size, limit=page_size)
    return [TerraformWorkspaceOut.model_validate(item) for item in items]


@router.get("/findings", response_model=TerraformFindingListResponse)
async def list_findings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    workspace_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    service: TerraformAnalysisService = Depends(get_terraform_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List Terraform findings."""
    skip = (page - 1) * page_size
    items = await service.finding_repo.list_findings(
        skip=skip,
        limit=page_size,
        workspace_id=workspace_id,
        severity=severity,
        category=category,
        status=status_filter,
    )
    total = await service.finding_repo.count_findings(
        workspace_id=workspace_id,
        severity=severity,
        category=category,
        status=status_filter,
    )
    return TerraformFindingListResponse(
        items=[TerraformFindingOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/findings/{finding_id}", response_model=TerraformFindingOut)
async def get_finding(
    finding_id: str,
    service: TerraformAnalysisService = Depends(get_terraform_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Get a Terraform finding detail."""
    finding = await service.finding_repo.get(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Terraform finding not found")
    return TerraformFindingOut.model_validate(finding)


@router.get("/drift", response_model=TerraformDriftListResponse)
async def list_drift(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    workspace_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    service: TerraformAnalysisService = Depends(get_terraform_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List Terraform drift records."""
    skip = (page - 1) * page_size
    items = await service.drift_repo.list_drift(
        skip=skip,
        limit=page_size,
        workspace_id=workspace_id,
        severity=severity,
        status=status_filter,
    )
    total = await service.drift_repo.count_drift(
        workspace_id=workspace_id,
        severity=severity,
        status=status_filter,
    )
    return TerraformDriftListResponse(
        items=[TerraformDriftOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/scans", response_model=list[TerraformScanOut])
async def list_scans(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: TerraformAnalysisService = Depends(get_terraform_service),
    _: CurrentUser = Depends(get_current_user),
):
    """List Terraform scans."""
    scans = await service.scan_repo.get_all(skip=(page - 1) * page_size, limit=page_size)
    return [TerraformScanOut.model_validate(scan) for scan in scans]


@router.get("/stats", response_model=TerraformDashboardStats)
async def get_stats(
    service: TerraformAnalysisService = Depends(get_terraform_service),
    _: CurrentUser = Depends(get_current_user),
):
    """Return Terraform security and drift dashboard statistics."""
    return await service.stats()
