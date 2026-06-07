"""Tests — enterprise audit trail and RBAC enforcement."""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from app.core.security import CurrentUser, create_access_token
from app.models.audit import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService


def _token(email: str, role: str) -> str:
    return create_access_token(subject=email, role=role)


@pytest.mark.asyncio
async def test_viewer_cannot_run_write_analysis_endpoint(client: AsyncClient):
    headers = {"Authorization": f"Bearer {_token('viewer@nexusops.ai', 'viewer')}"}

    response = await client.post(
        "/api/v1/optimization/analyze",
        headers=headers,
        json={"demo": True, "report_name": "viewer should not run analysis"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_register_cluster(client: AsyncClient):
    headers = {"Authorization": f"Bearer {_token('viewer@nexusops.ai', 'viewer')}"}

    response = await client.post(
        "/api/v1/clusters",
        headers=headers,
        json={
            "name": "viewer-denied",
            "display_name": "Viewer Denied",
            "provider": "demo",
            "environment": "development",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_audit_events_are_admin_only(client: AsyncClient, db_session):
    repo = AuditRepository(model=AuditEvent, session=db_session)
    await AuditService(repo).record(
        action="test.audit",
        actor=CurrentUser("admin@nexusops.ai", "admin@nexusops.ai", "admin"),
        resource_type="test",
        resource_id="resource-1",
        metadata={"timestamp": datetime.now(UTC).isoformat()},
    )

    viewer = {"Authorization": f"Bearer {_token('viewer@nexusops.ai', 'viewer')}"}
    denied = await client.get("/api/v1/audit/events", headers=viewer)
    assert denied.status_code == 403

    admin = {"Authorization": f"Bearer {_token('admin@nexusops.ai', 'admin')}"}
    allowed = await client.get("/api/v1/audit/events", headers=admin)
    assert allowed.status_code == 200
    body = allowed.json()
    assert body["total"] >= 1
    assert any(item["action"] == "test.audit" for item in body["items"])
