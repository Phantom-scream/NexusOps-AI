"""Tests — Telemetry providers, service ingestion, and APIs."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.cluster import Cluster
from app.models.telemetry import TelemetrySource
from app.repositories.cluster_repository import ClusterRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.services.telemetry_service import TelemetryService


async def _get_token(client: AsyncClient) -> str:
    suffix = uuid4().hex[:8]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"telemetry_test_{suffix}@nexusops.ai",
            "username": f"telemetryuser_{suffix}",
            "password": "Password1",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": f"telemetry_test_{suffix}@nexusops.ai",
            "password": "Password1",
        },
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_demo_telemetry_generation_uses_persisted_topology(db_session):
    service = TelemetryService(
        telemetry_repo=TelemetryRepository(model=TelemetrySource, session=db_session),
        cluster_repo=ClusterRepository(model=Cluster, session=db_session),
    )

    source, counts = await service.generate_demo_telemetry()
    await db_session.flush()

    assert source.source_type == "demo"
    assert counts["clusters"] >= 1
    assert counts["metrics"] > 0
    assert counts["logs"] > 0
    assert counts["events"] > 0
    assert counts["traces"] > 0

    metrics = await service.list_metrics(metric_name="cpu_usage_percent", limit=10)
    logs = await service.list_logs(limit=10)
    events = await service.list_events(limit=10)
    traces = await service.list_traces(limit=10)

    assert metrics
    assert logs
    assert events
    assert traces
    assert metrics[0].cluster_id is not None
    assert traces[0].trace_id


@pytest.mark.asyncio
async def test_demo_telemetry_api_and_cluster_filters(client: AsyncClient):
    token = await _get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    generated = await client.post("/api/v1/demo/telemetry/generate", headers=headers)
    assert generated.status_code == 200
    body = generated.json()
    assert body["metrics"] > 0
    assert body["source"]["source_type"] == "demo"

    metrics = await client.get("/api/v1/metrics?metric_name=cpu_usage_percent", headers=headers)
    assert metrics.status_code == 200
    assert len(metrics.json()) > 0

    cluster_id = metrics.json()[0]["cluster_id"]
    cluster_logs = await client.get(f"/api/v1/clusters/{cluster_id}/logs", headers=headers)
    cluster_events = await client.get(f"/api/v1/clusters/{cluster_id}/events", headers=headers)
    cluster_traces = await client.get(f"/api/v1/clusters/{cluster_id}/traces", headers=headers)

    assert cluster_logs.status_code == 200
    assert cluster_events.status_code == 200
    assert cluster_traces.status_code == 200
    assert all(row["cluster_id"] == cluster_id for row in cluster_logs.json())
