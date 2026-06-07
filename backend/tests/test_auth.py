"""Tests — Auth endpoints"""
import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings


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


@pytest.mark.asyncio
async def test_tokens_include_production_identity_claims(client: AsyncClient):
    payload = {
        "email": "claims@nexusops.ai",
        "username": "claimsuser",
        "password": "Password1",
    }
    await client.post("/api/v1/auth/register", json=payload)

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    token = resp.json()["access_token"]
    decoded = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE,
    )
    assert decoded["iss"] == settings.JWT_ISSUER
    assert decoded["aud"] == settings.JWT_AUDIENCE
    assert decoded["type"] == "access"
    assert decoded["jti"]


@pytest.mark.asyncio
async def test_refresh_preserves_database_role(client: AsyncClient):
    payload = {
        "email": "refresh@nexusops.ai",
        "username": "refreshuser",
        "password": "Password1",
    }
    await client.post("/api/v1/auth/register", json=payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )

    assert resp.status_code == 200
    decoded = jwt.decode(
        resp.json()["access_token"],
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE,
    )
    assert decoded["role"] == "viewer"
