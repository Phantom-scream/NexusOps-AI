"""Tests — Auth endpoints"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # Register
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@nexusops.ai",
        "username": "testuser",
        "password": "Password1",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@nexusops.ai"

    # Login
    resp = await client.post("/api/v1/auth/login", json={
        "email": "test@nexusops.ai",
        "password": "Password1",
    })
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@nexusops.ai",
        "password": "WrongPass1",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_duplicate_registration(client: AsyncClient):
    payload = {"email": "dup@nexusops.ai", "username": "dupuser", "password": "Password1"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
