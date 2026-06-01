"""Tests — AI investigation workflow."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.cluster import Cluster
from app.models.incident import Incident, IncidentAnalysis
from app.models.telemetry import TelemetrySource
from app.repositories.cluster_repository import ClusterRepository
from app.repositories.incident_repository import IncidentAnalysisRepository, IncidentRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.incident import IncidentCreate
from app.schemas.investigation import InvestigationCreate
from app.services.incident_service import IncidentService
from app.services.infrastructure_discovery_service import InfrastructureDiscoveryService
from app.services.investigation_service import InvestigationService
from app.services.telemetry_service import TelemetryService


async def _get_token(client: AsyncClient) -> str:
    suffix = uuid4().hex[:8]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"investigation_test_{suffix}@nexusops.ai",
            "username": f"investigationuser_{suffix}",
            "password": "Password1",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": f"investigation_test_{suffix}@nexusops.ai",
            "password": "Password1",
        },
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_investigation_service_collects_evidence_and_generates_rca(db_session):
    cluster_repo = ClusterRepository(model=Cluster, session=db_session)
    discovery = InfrastructureDiscoveryService(repository=cluster_repo)
    clusters = await discovery.generate_demo_environment()
    cluster = clusters[0]

    telemetry = TelemetryService(
        telemetry_repo=TelemetryRepository(model=TelemetrySource, session=db_session),
        cluster_repo=cluster_repo,
    )
    await telemetry.generate_demo_telemetry()

    incident_service = IncidentService(
        repository=IncidentRepository(model=Incident, session=db_session),
        analysis_repository=IncidentAnalysisRepository(model=IncidentAnalysis, session=db_session),
    )
    incident = await incident_service.create_incident(
        IncidentCreate(
            title="CrashLoopBackOff in demo checkout service",
            description="Demo pod restarts and degraded rollout require RCA.",
            severity="high",
            source="ai_detected",
            cluster_id=cluster.id,
            cluster_name=cluster.name,
        )
    )

    service = InvestigationService.from_session(db_session)
    investigation = await service.create_investigation(
        InvestigationCreate(
            incident_id=incident.id,
            cluster_id=cluster.id,
            query="Investigate pod restarts, failed deployment, logs, events, metrics, and traces.",
            run_immediately=True,
        )
    )

    evidence = await service.get_evidence(investigation.id)
    assert investigation.status == "completed"
    assert investigation.root_cause
    assert investigation.confidence_score is not None
    assert investigation.remediation_recommendations
    assert evidence


@pytest.mark.asyncio
async def test_investigation_api_demo_flow(client: AsyncClient):
    token = await _get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    generated = await client.post("/api/v1/demo/incidents/generate", headers=headers)
    assert generated.status_code == 200
    incidents = generated.json()
    assert incidents

    created = await client.post(
        "/api/v1/investigations",
        headers=headers,
        json={
            "incident_id": incidents[0]["id"],
            "cluster_id": incidents[0]["cluster_id"],
            "query": "Run a full root cause analysis using telemetry and topology.",
            "run_immediately": True,
        },
    )
    assert created.status_code == 201
    investigation = created.json()
    assert investigation["status"] == "completed"
    assert investigation["root_cause"]

    evidence = await client.get(f"/api/v1/investigations/{investigation['id']}/evidence", headers=headers)
    assert evidence.status_code == 200
    assert len(evidence.json()) > 0
