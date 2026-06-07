"""
NexusOps AI — User Model
"""
from enum import Enum

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    SECURITY_ANALYST = "security_analyst"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    """Platform user with RBAC roles."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)
    last_login_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
