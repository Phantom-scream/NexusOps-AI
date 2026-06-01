"""Repository helpers for AI investigations."""

from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.models.investigation import Investigation, InvestigationEvidence
from app.repositories.base import BaseRepository


class InvestigationRepository(BaseRepository[Investigation]):
    async def get_with_evidence(self, investigation_id: str) -> Investigation | None:
        result = await self.session.execute(
            select(Investigation)
            .where(Investigation.id == investigation_id)
            .options(selectinload(Investigation.evidence_items))
        )
        return result.scalar_one_or_none()

    async def list_investigations(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        incident_id: str | None = None,
        cluster_id: str | None = None,
        status: str | None = None,
    ) -> Sequence[Investigation]:
        stmt = select(Investigation).order_by(Investigation.created_at.desc())
        if incident_id:
            stmt = stmt.where(Investigation.incident_id == incident_id)
        if cluster_id:
            stmt = stmt.where(Investigation.cluster_id == cluster_id)
        if status:
            stmt = stmt.where(Investigation.status == status)
        result = await self.session.execute(stmt.offset(skip).limit(limit))
        return result.scalars().all()

    async def count_investigations(
        self,
        *,
        incident_id: str | None = None,
        cluster_id: str | None = None,
        status: str | None = None,
    ) -> int:
        filters = {}
        if incident_id:
            filters["incident_id"] = incident_id
        if cluster_id:
            filters["cluster_id"] = cluster_id
        if status:
            filters["status"] = status
        return await self.count(filters=filters)

    async def replace_evidence(
        self,
        investigation_id: str,
        evidence: list[InvestigationEvidence],
    ) -> list[InvestigationEvidence]:
        await self.session.execute(
            delete(InvestigationEvidence).where(InvestigationEvidence.investigation_id == investigation_id)
        )
        for item in evidence:
            item.investigation_id = investigation_id
        self.session.add_all(evidence)
        await self.session.flush()
        return evidence


class InvestigationEvidenceRepository(BaseRepository[InvestigationEvidence]):
    async def get_by_investigation(self, investigation_id: str) -> Sequence[InvestigationEvidence]:
        result = await self.session.execute(
            select(InvestigationEvidence)
            .where(InvestigationEvidence.investigation_id == investigation_id)
            .order_by(InvestigationEvidence.severity, InvestigationEvidence.created_at.desc())
        )
        return result.scalars().all()
