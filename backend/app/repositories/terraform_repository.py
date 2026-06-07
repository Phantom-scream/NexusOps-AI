"""Terraform security and drift repositories."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.security_finding import TerraformScan
from app.models.terraform import (
    TerraformDrift,
    TerraformFinding,
    TerraformPolicyViolation,
    TerraformResource,
    TerraformWorkspace,
)
from app.repositories.base import BaseRepository


class TerraformWorkspaceRepository(BaseRepository[TerraformWorkspace]):
    def __init__(self, session: AsyncSession):
        super().__init__(TerraformWorkspace, session)

    async def get_with_resources(self, workspace_id: str) -> TerraformWorkspace | None:
        stmt = (
            select(TerraformWorkspace)
            .options(selectinload(TerraformWorkspace.resources))
            .where(TerraformWorkspace.id == workspace_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class TerraformResourceRepository(BaseRepository[TerraformResource]):
    def __init__(self, session: AsyncSession):
        super().__init__(TerraformResource, session)

    async def list_for_workspace(self, workspace_id: str) -> Sequence[TerraformResource]:
        stmt = (
            select(TerraformResource)
            .where(TerraformResource.workspace_id == workspace_id)
            .order_by(TerraformResource.address.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class TerraformFindingRepository(BaseRepository[TerraformFinding]):
    def __init__(self, session: AsyncSession):
        super().__init__(TerraformFinding, session)

    async def list_findings(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        workspace_id: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> Sequence[TerraformFinding]:
        stmt = select(TerraformFinding)
        stmt = self._apply_filters(stmt, workspace_id, severity, category, status)
        stmt = stmt.order_by(TerraformFinding.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_findings(
        self,
        *,
        workspace_id: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(TerraformFinding)
        stmt = self._apply_filters(stmt, workspace_id, severity, category, status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def _apply_filters(self, stmt, workspace_id, severity, category, status):
        if workspace_id:
            stmt = stmt.where(TerraformFinding.workspace_id == workspace_id)
        if severity:
            stmt = stmt.where(TerraformFinding.severity == severity)
        if category:
            stmt = stmt.where(TerraformFinding.category == category)
        if status:
            stmt = stmt.where(TerraformFinding.status == status)
        return stmt


class TerraformDriftRepository(BaseRepository[TerraformDrift]):
    def __init__(self, session: AsyncSession):
        super().__init__(TerraformDrift, session)

    async def list_drift(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        workspace_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> Sequence[TerraformDrift]:
        stmt = select(TerraformDrift)
        if workspace_id:
            stmt = stmt.where(TerraformDrift.workspace_id == workspace_id)
        if severity:
            stmt = stmt.where(TerraformDrift.severity == severity)
        if status:
            stmt = stmt.where(TerraformDrift.status == status)
        stmt = stmt.order_by(TerraformDrift.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_drift(
        self,
        *,
        workspace_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(TerraformDrift)
        if workspace_id:
            stmt = stmt.where(TerraformDrift.workspace_id == workspace_id)
        if severity:
            stmt = stmt.where(TerraformDrift.severity == severity)
        if status:
            stmt = stmt.where(TerraformDrift.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one()


class TerraformScanRepository(BaseRepository[TerraformScan]):
    def __init__(self, session: AsyncSession):
        super().__init__(TerraformScan, session)


class TerraformPolicyViolationRepository(BaseRepository[TerraformPolicyViolation]):
    def __init__(self, session: AsyncSession):
        super().__init__(TerraformPolicyViolation, session)
