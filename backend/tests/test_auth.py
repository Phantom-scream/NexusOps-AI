"""Tests — Auth endpoints"""
import pytest
from httpx import AsyncClient
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit import AuditEvent


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
    assert decoded["role"] == settings.default_registered_role


@pytest.mark.asyncio
async def test_logout_records_audit_event(client: AsyncClient, db_session: AsyncSession):
    payload = {
        "email": "logout@nexusops.ai",
        "username": "logoutuser",
        "password": "Password1",
    }
    await client.post("/api/v1/auth/register", json=payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password"]},
    )

    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert resp.status_code == 204
    result = await db_session.execute(
        select(AuditEvent).where(AuditEvent.action == "auth.logout")
    )
    assert result.scalar_one().actor_email == payload["email"]
