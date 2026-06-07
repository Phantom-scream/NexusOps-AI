"""Tests — Terraform security and drift analysis."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.schemas.terraform import TerraformAnalyzeRequest
from app.services.terraform_service import TerraformAnalysisService


async def _get_token(client: AsyncClient) -> str:
    suffix = uuid4().hex[:8]
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"terraform_test_{suffix}@nexusops.ai",
            "username": f"terraformuser_{suffix}",
            "password": "Password1",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": f"terraform_test_{suffix}@nexusops.ai",
            "password": "Password1",
        },
    )
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_terraform_service_demo_analysis_generates_findings_and_drift(db_session):
    service = TerraformAnalysisService.from_session(db_session)

    workspace, scan, resources, findings, drift, policy_violations, stats = await service.analyze(
        TerraformAnalyzeRequest(demo=True)
    )

    assert workspace.name == "demo-enterprise-terraform"
    assert scan.status == "completed"
    assert resources
    assert findings
    assert drift
    assert policy_violations
    assert stats.total_findings >= len(findings)
    assert any(item.category == "iam" for item in findings)
    assert any(item.category == "secrets" for item in findings)
    assert any(item.attribute_path.endswith("replicas") for item in drift)


@pytest.mark.asyncio
async def test_terraform_api_demo_analysis_flow(client: AsyncClient):
    token = await _get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    analyzed = await client.post(
        "/api/v1/terraform/analyze",
        headers=headers,
        json={"demo": True, "scan_name": "API demo terraform analysis"},
    )
    assert analyzed.status_code == 200
    body = analyzed.json()
    assert body["scan"]["status"] == "completed"
    assert body["findings"]
    assert body["drift"]

    findings = await client.get("/api/v1/terraform/findings", headers=headers)
    assert findings.status_code == 200
    assert findings.json()["total"] > 0

    drift = await client.get("/api/v1/terraform/drift", headers=headers)
    assert drift.status_code == 200
    assert drift.json()["total"] > 0
