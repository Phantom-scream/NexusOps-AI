"""Repositories for cost optimization and resource intelligence."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost_recommendation import (
    CostRecommendation,
    OptimizationFinding,
    OptimizationReport,
    OptimizationRule,
    ResourceUtilization,
)
from app.repositories.base import BaseRepository


class ResourceUtilizationRepository(BaseRepository[ResourceUtilization]):
    def __init__(self, session: AsyncSession):
        super().__init__(ResourceUtilization, session)


class OptimizationRuleRepository(BaseRepository[OptimizationRule]):
    def __init__(self, session: AsyncSession):
        super().__init__(OptimizationRule, session)

    async def get_by_name(self, name: str) -> OptimizationRule | None:
        result = await self.session.execute(select(OptimizationRule).where(OptimizationRule.name == name))
        return result.scalar_one_or_none()


class OptimizationFindingRepository(BaseRepository[OptimizationFinding]):
    def __init__(self, session: AsyncSession):
        super().__init__(OptimizationFinding, session)

    async def list_findings(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        cluster_id: str | None = None,
        severity: str | None = None,
        finding_type: str | None = None,
        status: str | None = None,
    ) -> Sequence[OptimizationFinding]:
        stmt = select(OptimizationFinding)
        stmt = self._apply_filters(stmt, cluster_id, severity, finding_type, status)
        stmt = stmt.order_by(OptimizationFinding.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_findings(
        self,
        *,
        cluster_id: str | None = None,
        severity: str | None = None,
        finding_type: str | None = None,
        status: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(OptimizationFinding)
        stmt = self._apply_filters(stmt, cluster_id, severity, finding_type, status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def _apply_filters(self, stmt, cluster_id, severity, finding_type, status):
        if cluster_id:
            stmt = stmt.where(OptimizationFinding.cluster_id == cluster_id)
        if severity:
            stmt = stmt.where(OptimizationFinding.severity == severity)
        if finding_type:
            stmt = stmt.where(OptimizationFinding.finding_type == finding_type)
        if status:
            stmt = stmt.where(OptimizationFinding.status == status)
        return stmt


class CostRecommendationRepository(BaseRepository[CostRecommendation]):
    def __init__(self, session: AsyncSession):
        super().__init__(CostRecommendation, session)

    async def list_recommendations(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        cluster_id: str | None = None,
        optimization_type: str | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> Sequence[CostRecommendation]:
        stmt = select(CostRecommendation)
        stmt = self._apply_filters(stmt, cluster_id, optimization_type, severity, status)
        stmt = stmt.order_by(CostRecommendation.estimated_monthly_savings_usd.desc().nullslast()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_recommendations(
        self,
        *,
        cluster_id: str | None = None,
        optimization_type: str | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(CostRecommendation)
        stmt = self._apply_filters(stmt, cluster_id, optimization_type, severity, status)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    def _apply_filters(self, stmt, cluster_id, optimization_type, severity, status):
        if cluster_id:
            stmt = stmt.where(CostRecommendation.cluster_id == cluster_id)
        if optimization_type:
            stmt = stmt.where(CostRecommendation.optimization_type == optimization_type)
        if severity:
            stmt = stmt.where(CostRecommendation.severity == severity)
        if status:
            stmt = stmt.where(CostRecommendation.status == status)
        return stmt


class OptimizationReportRepository(BaseRepository[OptimizationReport]):
    def __init__(self, session: AsyncSession):
        super().__init__(OptimizationReport, session)
