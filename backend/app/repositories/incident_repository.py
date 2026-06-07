"""
NexusOps AI — Incident Repository
"""
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.incident import Incident, IncidentAnalysis
from app.repositories.base import BaseRepository


class IncidentRepository(BaseRepository[Incident]):

    async def get_with_analyses(self, incident_id: str) -> Incident | None:
        result = await self.session.execute(
            select(Incident)
            .where(Incident.id == incident_id)
            .options(selectinload(Incident.analyses))
        )
        return result.scalar_one_or_none()

    async def get_by_cluster(
        self,
        cluster_id: str,
        status: str | None = None,
        severity: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[Incident]:
        stmt = select(Incident).where(Incident.cluster_id == cluster_id)
        if status:
            stmt = stmt.where(Incident.status == status)
        if severity:
            stmt = stmt.where(Incident.severity == severity)
        stmt = stmt.offset(skip).limit(limit).order_by(Incident.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_open_critical(self) -> Sequence[Incident]:
        result = await self.session.execute(
            select(Incident)
            .where(Incident.status == "open", Incident.severity.in_(["critical", "high"]))
            .order_by(Incident.created_at.desc())
            .limit(20)
        )
        return result.scalars().all()


class IncidentAnalysisRepository(BaseRepository[IncidentAnalysis]):

    async def get_by_incident(self, incident_id: str) -> Sequence[IncidentAnalysis]:
        result = await self.session.execute(
            select(IncidentAnalysis)
            .where(IncidentAnalysis.incident_id == incident_id)
            .order_by(IncidentAnalysis.created_at.desc())
        )
        return result.scalars().all()
