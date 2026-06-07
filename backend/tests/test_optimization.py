"""Tests — cost optimization and resource intelligence."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.schemas.optimization import OptimizationAnalyzeRequest
from app.services.optimization_service import OptimizationService


async def _get_token(client: AsyncClient) -> str:
    suffix = uuid4().hex[:8]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"optimization_test_{suffix}@nexusops.ai",
            "username": f"optimizationuser_{suffix}",
            "password": "Password1",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": f"optimization_test_{suffix}@nexusops.ai",
            "password": "Password1",
        },
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_optimization_service_demo_analysis_generates_recommendations(db_session):
    service = OptimizationService.from_session(db_session)

    report, findings, recommendations, utilization, stats = await service.analyze(
        OptimizationAnalyzeRequest(demo=True, report_name="Test optimization report")
    )

    assert report.status == "completed"
    assert utilization
    assert findings
    assert recommendations
    assert report.estimated_monthly_savings_usd > 0
    assert stats.estimated_monthly_savings_usd >= report.estimated_monthly_savings_usd
    assert any(item.optimization_type == "idle_removal" for item in recommendations)
    assert any(item.recommended_replicas == 0 for item in recommendations)


@pytest.mark.asyncio
async def test_optimization_api_demo_flow(client: AsyncClient):
    token = await _get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    analyzed = await client.post(
        "/api/v1/optimization/analyze",
        headers=headers,
        json={"demo": True, "report_name": "API optimization report"},
    )
    assert analyzed.status_code == 200
    body = analyzed.json()
    assert body["report"]["status"] == "completed"
    assert body["recommendations"]
    assert body["findings"]

    recommendations = await client.get("/api/v1/optimization/recommendations", headers=headers)
    assert recommendations.status_code == 200
    assert recommendations.json()["total"] > 0

    findings = await client.get("/api/v1/optimization/findings", headers=headers)
    assert findings.status_code == 200
    assert findings.json()["total"] > 0

    reports = await client.get("/api/v1/optimization/reports", headers=headers)
    assert reports.status_code == 200
    assert reports.json()["total"] > 0
