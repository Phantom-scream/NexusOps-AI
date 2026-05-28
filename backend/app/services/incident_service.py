"""
NexusOps AI — Incident Service
Business logic for incident lifecycle management
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from app.models.incident import Incident, IncidentAnalysis, IncidentStatus
from app.repositories.incident_repository import IncidentAnalysisRepository, IncidentRepository
from app.schemas.incident import IncidentCreate, IncidentUpdate

logger = structlog.get_logger(__name__)


class IncidentService:
    """
    Manages incident lifecycle, AI analysis triggers, and escalation logic.
    """

    def __init__(
        self,
        repository: IncidentRepository,
        analysis_repository: IncidentAnalysisRepository,
    ):
        self.repo = repository
        self.analysis_repo = analysis_repository

    async def create_incident(self, data: IncidentCreate) -> Incident:
        incident = Incident(
            id=str(uuid.uuid4()),
            title=data.title,
            description=data.description,
            severity=data.severity,
            source=data.source,
            cluster_id=data.cluster_id,
            cluster_name=data.cluster_name,
            namespace=data.namespace,
            affected_workload=data.affected_workload,
            tags=data.tags or [],
            status=IncidentStatus.OPEN,
        )
        created = await self.repo.create(incident)
        logger.info(
            "Incident created",
            incident_id=created.id,
            severity=created.severity,
            title=created.title,
        )
        return created

    async def get_incident(self, incident_id: str) -> Optional[Incident]:
        return await self.repo.get_with_analyses(incident_id)

    async def list_incidents(
        self,
        skip: int = 0,
        limit: int = 50,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        cluster_id: Optional[str] = None,
    ) -> tuple[List[Incident], int]:
        filters: Dict[str, Any] = {}
        if severity:
            filters["severity"] = severity
        if status:
            filters["status"] = status
        if cluster_id:
            filters["cluster_id"] = cluster_id

        incidents = await self.repo.get_all(skip=skip, limit=limit, filters=filters)
        total = await self.repo.count(filters=filters)
        return list(incidents), total

    async def update_incident(
        self, incident_id: str, data: IncidentUpdate
    ) -> Optional[Incident]:
        incident = await self.repo.get(incident_id)
        if not incident:
            return None
        updates = data.model_dump(exclude_none=True)
        return await self.repo.update(incident, updates)

    async def resolve_incident(self, incident_id: str, resolved_by: str) -> Optional[Incident]:
        incident = await self.repo.get(incident_id)
        if not incident:
            return None
        incident.status = IncidentStatus.RESOLVED
        await self.repo.save(incident)
        logger.info("Incident resolved", incident_id=incident_id, resolved_by=resolved_by)
        return incident

    async def save_analysis_result(
        self,
        incident_id: str,
        query: str,
        analysis_result: Dict[str, Any],
    ) -> IncidentAnalysis:
        """Persist an AI analysis result and update the incident's root cause."""
        analysis = IncidentAnalysis(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            query=query,
            analysis=analysis_result.get("analysis", ""),
            root_cause_summary=analysis_result.get("root_cause"),
            remediation_yaml=analysis_result.get("remediation_yaml"),
            confidence_score=analysis_result.get("confidence"),
            tokens_used=analysis_result.get("tokens_used"),
            llm_model=analysis_result.get("model"),
            context_sources=analysis_result.get("context_sources", []),
        )
        saved = await self.analysis_repo.create(analysis)

        # Update parent incident with AI findings
        incident = await self.repo.get(incident_id)
        if incident:
            incident.root_cause = analysis_result.get("root_cause")
            incident.ai_confidence = analysis_result.get("confidence")
            incident.ai_analysis_id = saved.id
            if incident.status == IncidentStatus.OPEN:
                incident.status = IncidentStatus.INVESTIGATING
            await self.repo.save(incident)

        logger.info("Analysis saved", incident_id=incident_id, confidence=analysis.confidence_score)
        return saved

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Stats for the incident dashboard."""
        total = await self.repo.count()
        open_count = await self.repo.count({"status": "open"})
        critical_open = await self.repo.count({"status": "open", "severity": "critical"})
        high_open = await self.repo.count({"status": "open", "severity": "high"})
        resolved = await self.repo.count({"status": "resolved"})

        recent = await self.repo.get_open_critical()

        return {
            "total": total,
            "open": open_count,
            "critical_open": critical_open,
            "high_open": high_open,
            "resolved": resolved,
            "recent_critical": [
                {
                    "id": inc.id,
                    "title": inc.title,
                    "severity": inc.severity,
                    "cluster_name": inc.cluster_name,
                    "created_at": inc.created_at.isoformat(),
                }
                for inc in recent[:5]
            ],
        }
