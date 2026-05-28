"""
NexusOps AI — User Model
"""
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin):
    """Platform user with RBAC roles."""
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(30), default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    last_login_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
