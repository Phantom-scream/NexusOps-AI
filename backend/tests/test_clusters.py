"""Tests — Cluster endpoints"""
import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient) -> str:
    await client.post("/api/v1/auth/register", json={
        "email": "cluster_test@nexusops.ai",
        "username": "clusteruser",
        "password": "Password1",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "cluster_test@nexusops.ai",
        "password": "Password1",
    })
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_list_clusters_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/clusters")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_clusters_empty(client: AsyncClient):
    token = await _get_token(client)
    resp = await client.get("/api/v1/clusters", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
