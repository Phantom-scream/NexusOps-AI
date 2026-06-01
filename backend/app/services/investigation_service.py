"""AI incident investigation workflow orchestration."""

import json
from datetime import UTC, datetime
from uuid import uuid4

import structlog

from app.ai.context_builder import ContextBuilder
from app.ai.evidence_collector import EvidenceCollector
from app.ai.llm_providers import LLMProviderFactory
from app.ai.prompts.templates import INCIDENT_INVESTIGATION_SYSTEM_PROMPT
from app.ai.rag_pipeline import RAGPipeline
from app.ai.remediation_engine import RemediationEngine
from app.core.config import settings
from app.models.cluster import Cluster
from app.models.incident import Incident, IncidentAnalysis, IncidentStatus
from app.models.investigation import Investigation, InvestigationEvidence
from app.models.telemetry import TelemetrySource
from app.repositories.cluster_repository import ClusterRepository
from app.repositories.incident_repository import IncidentAnalysisRepository, IncidentRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.investigation import InvestigationCreate

logger = structlog.get_logger(__name__)


class InvestigationService:
    """Runs the full incident investigation pipeline."""

    def __init__(
        self,
        investigation_repo: InvestigationRepository,
        incident_repo: IncidentRepository,
        incident_analysis_repo: IncidentAnalysisRepository,
        cluster_repo: ClusterRepository,
        telemetry_repo: TelemetryRepository,
    ):
        self.investigation_repo = investigation_repo
        self.incident_repo = incident_repo
        self.incident_analysis_repo = incident_analysis_repo
        self.cluster_repo = cluster_repo
        self.telemetry_repo = telemetry_repo
        self.evidence_collector = EvidenceCollector(telemetry_repo=telemetry_repo)
        self.context_builder = ContextBuilder(cluster_repo=cluster_repo, incident_repo=incident_repo)
        self.remediation_engine = RemediationEngine()
        self.rag = RAGPipeline()

    @classmethod
    def from_session(cls, session):
        return cls(
            investigation_repo=InvestigationRepository(model=Investigation, session=session),
            incident_repo=IncidentRepository(model=Incident, session=session),
            incident_analysis_repo=IncidentAnalysisRepository(model=IncidentAnalysis, session=session),
            cluster_repo=ClusterRepository(model=Cluster, session=session),
            telemetry_repo=TelemetryRepository(model=TelemetrySource, session=session),
        )

    async def create_investigation(self, data: InvestigationCreate) -> Investigation:
        incident = await self.incident_repo.get(data.incident_id) if data.incident_id else None
        title = data.title or (f"Investigation: {incident.title}" if incident else "Ad-hoc AI Investigation")
        investigation = Investigation(
            id=str(uuid4()),
            incident_id=data.incident_id,
            cluster_id=data.cluster_id or (incident.cluster_id if incident else None),
            title=title,
            query=data.query,
            status="created",
            severity=incident.severity if incident else "medium",
        )
        await self.investigation_repo.create(investigation)
        if data.run_immediately:
            return await self.run_investigation(investigation.id)
        return investigation

    async def run_investigation(self, investigation_id: str) -> Investigation:
        investigation = await self.investigation_repo.get_with_evidence(investigation_id)
        if not investigation:
            raise ValueError("Investigation not found")

        investigation.status = "running"
        investigation.started_at = datetime.now(UTC)
        await self.investigation_repo.save(investigation)

        incident = await self.incident_repo.get(investigation.incident_id) if investigation.incident_id else None
        evidence = await self.evidence_collector.collect(incident, investigation.cluster_id)
        context = await self.context_builder.build(
            incident=incident,
            cluster_id=investigation.cluster_id,
            query=investigation.query,
            evidence=evidence,
        )
        await self.investigation_repo.replace_evidence(investigation.id, evidence)

        analysis = await self._analyze(context=context, evidence=evidence)
        remediation = self.remediation_engine.recommend(evidence, analysis.get("root_cause"))
        if not analysis.get("remediation_recommendations"):
            analysis["remediation_recommendations"] = remediation

        investigation.summary = analysis.get("summary")
        investigation.root_cause = analysis.get("root_cause")
        investigation.root_cause_detail = analysis.get("root_cause_detail")
        investigation.severity = analysis.get("severity") or investigation.severity
        investigation.confidence_score = analysis.get("confidence")
        investigation.affected_resources = analysis.get("affected_resources") or self._affected_resources(evidence)
        investigation.supporting_evidence = analysis.get("supporting_evidence") or [self._evidence_summary(item) for item in evidence[:12]]
        investigation.remediation_recommendations = analysis.get("remediation_recommendations") or remediation
        investigation.investigation_context = context
        investigation.context_sources = ["topology", "metrics", "logs", "events", "traces", "incidents"]
        investigation.llm_provider = analysis.get("provider")
        investigation.llm_model = analysis.get("model")
        investigation.tokens_used = analysis.get("tokens_used")
        investigation.status = "completed"
        investigation.completed_at = datetime.now(UTC)
        await self.investigation_repo.save(investigation)

        if incident:
            await self._update_incident(incident, investigation)
            await self._save_incident_analysis(incident, investigation)
            await self._index_investigation(incident, investigation)

        logger.info("Investigation completed", investigation_id=investigation.id, confidence=investigation.confidence_score)
        return investigation

    async def list_investigations(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        incident_id: str | None = None,
        cluster_id: str | None = None,
        status: str | None = None,
    ) -> tuple[list[Investigation], int]:
        items = await self.investigation_repo.list_investigations(
            skip=skip,
            limit=limit,
            incident_id=incident_id,
            cluster_id=cluster_id,
            status=status,
        )
        total = await self.investigation_repo.count_investigations(
            incident_id=incident_id,
            cluster_id=cluster_id,
            status=status,
        )
        return list(items), total

    async def get_investigation(self, investigation_id: str) -> Investigation | None:
        return await self.investigation_repo.get_with_evidence(investigation_id)

    async def get_evidence(self, investigation_id: str) -> list[InvestigationEvidence]:
        investigation = await self.investigation_repo.get_with_evidence(investigation_id)
        return list(investigation.evidence_items) if investigation else []

    async def _analyze(self, *, context: dict, evidence: list[InvestigationEvidence]) -> dict:
        prompt = json.dumps(context, default=str)[:12000]
        provider = LLMProviderFactory.create()
        if provider.provider_name == "openai" and not self._has_openai_key():
            return self._fallback_analysis(context, evidence, f"{provider.provider_name}:not_configured")
        try:
            response = await provider.analyze(
                system_prompt=INCIDENT_INVESTIGATION_SYSTEM_PROMPT,
                user_message=f"Analyze this NexusOps investigation context and return valid JSON only:\n{prompt}",
            )
            parsed = self._parse_json(response.get("content", ""))
            parsed["provider"] = provider.provider_name
            parsed["model"] = response.get("model")
            parsed["tokens_used"] = response.get("tokens_used")
            return parsed
        except Exception as exc:
            logger.warning("LLM analysis failed; using deterministic investigation fallback", error=str(exc))
            return self._fallback_analysis(context, evidence, provider.provider_name)

    def _fallback_analysis(self, context: dict, evidence: list[InvestigationEvidence], provider_name: str) -> dict:
        top = evidence[0] if evidence else None
        incident = context.get("incident") or {}
        root = top.description if top else "No high-signal evidence was available for automated analysis."
        if top and top.evidence_type == "metric":
            root = f"{top.title}. This telemetry anomaly is the strongest correlated signal for the incident."
        elif top and top.evidence_type == "log":
            root = f"Application log evidence indicates: {top.description}"
        elif top and top.evidence_type == "event":
            root = f"Kubernetes event correlation points to {top.title}: {top.description}"
        elif top and top.evidence_type == "trace":
            root = f"Distributed trace evidence shows a slow or failed span: {top.description}"

        confidence = min(0.92, 0.45 + 0.08 * min(len(evidence), 5))
        severity = top.severity if top and top.severity in {"critical", "high", "medium", "low"} else incident.get("severity", "medium")
        remediation = self.remediation_engine.recommend(evidence, root)
        return {
            "summary": f"Investigation reviewed {len(evidence)} evidence items for {incident.get('title') or 'the selected infrastructure issue'}.",
            "root_cause": root,
            "root_cause_detail": "Deterministic analysis was used because the configured LLM provider was unavailable or not configured. The result is based on topology, telemetry, events, logs, and trace correlation.",
            "severity": severity,
            "confidence": round(confidence, 2),
            "affected_resources": self._affected_resources(evidence),
            "supporting_evidence": [self._evidence_summary(item) for item in evidence[:12]],
            "remediation_recommendations": remediation,
            "provider": f"{provider_name}:fallback",
            "model": "nexusops-deterministic-rca",
            "tokens_used": None,
        }

    def _parse_json(self, content: str) -> dict:
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.removeprefix("json").strip()
        parsed = json.loads(content)
        return {
            "summary": parsed.get("summary") or parsed.get("root_cause"),
            "root_cause": parsed.get("root_cause"),
            "root_cause_detail": parsed.get("root_cause_detail"),
            "severity": parsed.get("severity", "medium"),
            "confidence": parsed.get("confidence", 0.5),
            "affected_resources": parsed.get("affected_resources", []),
            "supporting_evidence": parsed.get("supporting_evidence") or parsed.get("evidence", []),
            "remediation_recommendations": self._normalize_remediation(parsed.get("remediation")),
        }

    def _normalize_remediation(self, remediation) -> list[dict]:
        if isinstance(remediation, list):
            return remediation
        if isinstance(remediation, dict):
            return [
                {"priority": index + 1, "category": key, "title": key.replace("_", " ").title(), "description": value}
                for index, (key, value) in enumerate(remediation.items())
            ]
        return []

    def _affected_resources(self, evidence: list[InvestigationEvidence]) -> list[dict]:
        seen = set()
        resources = []
        for item in evidence:
            key = (item.resource_type, item.resource_name, item.namespace_name)
            if item.resource_name and key not in seen:
                seen.add(key)
                resources.append(
                    {
                        "type": item.resource_type,
                        "name": item.resource_name,
                        "namespace": item.namespace_name,
                        "severity": item.severity,
                    }
                )
        return resources[:12]

    def _evidence_summary(self, item: InvestigationEvidence) -> dict:
        return {
            "type": item.evidence_type,
            "severity": item.severity,
            "title": item.title,
            "description": item.description,
            "resource": item.resource_name,
            "observed_at": item.observed_at.isoformat() if item.observed_at else None,
        }

    async def _update_incident(self, incident: Incident, investigation: Investigation) -> None:
        incident.root_cause = investigation.root_cause
        incident.ai_confidence = investigation.confidence_score
        incident.ai_analysis_id = investigation.id
        incident.remediation_steps = investigation.remediation_recommendations
        if incident.status == IncidentStatus.OPEN:
            incident.status = IncidentStatus.INVESTIGATING
        await self.incident_repo.save(incident)

    async def _save_incident_analysis(self, incident: Incident, investigation: Investigation) -> None:
        analysis = IncidentAnalysis(
            id=str(uuid4()),
            incident_id=incident.id,
            query=investigation.query,
            analysis=investigation.root_cause_detail or investigation.summary or "",
            root_cause_summary=investigation.root_cause,
            remediation_yaml=json.dumps(investigation.remediation_recommendations or []),
            confidence_score=investigation.confidence_score,
            tokens_used=investigation.tokens_used,
            llm_model=investigation.llm_model,
            context_sources=investigation.context_sources or [],
        )
        await self.incident_analysis_repo.create(analysis)

    async def _index_investigation(self, incident: Incident, investigation: Investigation) -> None:
        if not self._has_openai_key() and settings.LLM_PROVIDER != "ollama":
            return
        content = "\n".join(
            [
                incident.title,
                investigation.summary or "",
                investigation.root_cause or "",
                json.dumps(investigation.supporting_evidence or [])[:2000],
            ]
        )
        await self.rag.index_incident(
            incident_id=investigation.id,
            content=content,
            metadata={"source": "investigation", "incident_id": incident.id, "cluster_id": incident.cluster_id},
        )

    def _has_openai_key(self) -> bool:
        return bool(settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-your-"))
