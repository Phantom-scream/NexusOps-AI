"""
NexusOps AI — Security API
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import CurrentUser, get_current_user, require_security_analyst
from app.models.audit import AuditEvent
from app.models.security_finding import SecurityFinding, TerraformScan
from app.repositories.audit_repository import AuditRepository
from app.repositories.base import BaseRepository
from app.schemas.security import (
    SecurityFindingListResponse,
    SecurityFindingOut,
    TerraformScanOut,
    TerraformScanRequest,
)
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/findings", response_model=SecurityFindingListResponse)
async def list_findings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    cluster_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """List security findings with optional filters."""
    repo = BaseRepository(model=SecurityFinding, session=db)
    filters = {}
    if severity:
        filters["severity"] = severity
    if category:
        filters["category"] = category
    if cluster_id:
        filters["cluster_id"] = cluster_id

    skip = (page - 1) * page_size
    findings = await repo.get_all(skip=skip, limit=page_size, filters=filters)
    total = await repo.count(filters=filters)

    return SecurityFindingListResponse(
        items=[SecurityFindingOut.model_validate(f) for f in findings],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/dashboard")
async def get_security_dashboard(
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """Get security dashboard statistics."""
    repo = BaseRepository(model=SecurityFinding, session=db)

    total = await repo.count()
    critical = await repo.count({"severity": "critical"})
    high = await repo.count({"severity": "high"})
    medium = await repo.count({"severity": "medium"})
    low = await repo.count({"severity": "low"})
    open_count = await repo.count({"status": "open"})
    remediated = await repo.count({"status": "remediated"})

    recent = await repo.get_all(limit=10, filters={"status": "open"})

    return {
        "total_findings": total,
        "critical_findings": critical,
        "high_findings": high,
        "medium_findings": medium,
        "low_findings": low,
        "open_findings": open_count,
        "remediated_findings": remediated,
        "recent_findings": [SecurityFindingOut.model_validate(f) for f in recent],
    }


@router.post("/terraform/scan", status_code=status.HTTP_202_ACCEPTED)
async def trigger_terraform_scan(
    request: TerraformScanRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_security_analyst),
):
    """Submit a Terraform configuration for AI security analysis."""
    if not request.terraform_content:
        raise HTTPException(status_code=400, detail="terraform_content is required")

    scan = TerraformScan(
        id=str(uuid.uuid4()),
        scan_name=request.scan_name,
        repository_url=request.repository_url,
        branch=request.branch,
        scan_path=request.scan_path,
        status="queued",
    )
    db.add(scan)
    await db.flush()

    from app.workers.analysis_tasks import run_terraform_scan_task
    run_terraform_scan_task.delay(
        scan_id=scan.id,
        terraform_content=request.terraform_content,
        scan_name=request.scan_name,
        repo_url=request.repository_url,
    )

    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="security.terraform_scan",
        actor=current_user,
        request=http_request,
        resource_type="terraform_scan",
        resource_id=scan.id,
        metadata={"scan_name": scan.scan_name, "repository_url": scan.repository_url},
    )
    return TerraformScanOut.model_validate(scan)


@router.get("/terraform/scans", response_model=list[TerraformScanOut])
async def list_terraform_scans(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _: CurrentUser = Depends(get_current_user),
):
    """List past Terraform security scans."""
    repo = BaseRepository(model=TerraformScan, session=db)
    scans = await repo.get_all(skip=skip, limit=limit)
    return [TerraformScanOut.model_validate(s) for s in scans]
