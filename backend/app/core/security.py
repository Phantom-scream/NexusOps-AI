"""
NexusOps AI — Security Utilities
JWT authentication, password hashing, RBAC
"""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import UserRole

logger = structlog.get_logger(__name__)

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme. auto_error=False lets NexusOps return a consistent 401
# for missing credentials instead of FastAPI's default 403.
security_scheme = HTTPBearer(auto_error=False)


# ----------------------------------------------------------
# Password Utilities
# ----------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ----------------------------------------------------------
# JWT Token Utilities
# ----------------------------------------------------------

def create_access_token(
    subject: str,
    role: str = "viewer",
    extra_claims: dict | None = None,
) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(uuid4()),
        "type": "access",
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a signed JWT refresh token."""
    now = datetime.now(UTC)
    expire = now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": str(uuid4()),
        "type": "refresh",
    }

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            audience=settings.JWT_AUDIENCE,
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT decode failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ----------------------------------------------------------
# FastAPI Dependencies
# ----------------------------------------------------------

class CurrentUser:
    """Represents the authenticated user extracted from JWT."""

    def __init__(self, user_id: str, email: str, role: str):
        self.user_id = user_id
        self.email = email
        self.role = role

    @property
    def is_admin(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)

    @property
    def is_operator(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.OPERATOR)

    @property
    def is_security_analyst(self) -> bool:
        return self.role in (
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN,
            UserRole.OPERATOR,
            UserRole.SECURITY_ANALYST,
        )

    def has_any_role(self, *roles: str) -> bool:
        return self.role in roles or self.role == UserRole.SUPER_ADMIN


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> CurrentUser:
    """FastAPI dependency to extract and validate the current user from JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("sub")
    role = payload.get("role", "viewer")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return CurrentUser(user_id=user_id, email=user_id, role=role)


async def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require admin role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


async def require_operator(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require operator or admin role."""
    if not current_user.is_operator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator privileges required",
        )
    return current_user


async def require_security_analyst(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Require security analyst, operator, or admin role."""
    if not current_user.is_security_analyst:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Security analyst privileges required",
        )
    return current_user


def require_roles(*roles: str):
    """Return a FastAPI dependency requiring one of the supplied roles."""
    allowed = tuple(roles)

    async def dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current_user.has_any_role(*allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: one of {', '.join(allowed)}",
            )
        return current_user

    return dependency
