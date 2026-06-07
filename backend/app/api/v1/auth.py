"""
NexusOps AI — Authentication API
"""
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    CurrentUser,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.audit import AuditEvent
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.user import RefreshRequest, TokenResponse, UserLogin, UserOut, UserRegister
from app.services.audit_service import AuditService

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account."""
    # Check if email already taken
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=settings.default_registered_role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="auth.register",
        request=request,
        resource_type="user",
        resource_id=user.id,
        metadata={"email": user.email, "role": user.role},
    )
    logger.info("User registered", user_id=user.id, email=user.email)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate and return JWT tokens."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        logger.warning("User login failed", email=data.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    # Update last login
    user.last_login_at = datetime.now(UTC).isoformat()
    await db.flush()

    access_token = create_access_token(subject=user.email, role=user.role)
    refresh_token = create_refresh_token(subject=user.email)

    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="auth.login",
        actor=CurrentUser(user_id=user.email, email=user.email, role=user.role),
        request=request,
        resource_type="user",
        resource_id=user.id,
        metadata={"role": user.role},
    )
    logger.info("User logged in", user_id=user.id, role=user.role)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a refresh token for a new access token."""
    payload = decode_token(data.refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid token type")

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.email == subject))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not active")

    new_access_token = create_access_token(subject=user.email, role=user.role)
    new_refresh_token = create_refresh_token(subject=subject)

    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="auth.token_refresh",
        actor=CurrentUser(user_id=user.email, email=user.email, role=user.role),
        request=request,
        resource_type="user",
        resource_id=user.id,
        metadata={"role": user.role},
    )
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserOut)
async def get_me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current authenticated user's profile."""
    result = await db.execute(select(User).where(User.email == current_user.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a logout event for auditability."""
    await AuditService(AuditRepository(model=AuditEvent, session=db)).record(
        action="auth.logout",
        actor=current_user,
        request=request,
        resource_type="user",
        resource_id=current_user.user_id,
    )
    logger.info("User logged out", user_id=current_user.user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
