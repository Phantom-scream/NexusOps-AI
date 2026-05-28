"""
NexusOps AI — Base Repository
Generic CRUD operations using the Repository pattern
"""
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)

logger = structlog.get_logger(__name__)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository providing common CRUD operations.
    Subclass this for domain-specific repositories.
    """

    def __init__(self, model: Type[ModelT], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: str) -> Optional[ModelT]:
        """Fetch a single record by primary key."""
        result = await self.session.get(self.model, id)
        return result

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Sequence[ModelT]:
        """Fetch paginated list of records with optional equality filters."""
        stmt = select(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    stmt = stmt.where(getattr(self.model, field) == value)

        stmt = stmt.offset(skip).limit(limit).order_by(self.model.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        stmt = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    stmt = stmt.where(getattr(self.model, field) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, obj: ModelT) -> ModelT:
        """Persist a new record."""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelT, updates: Dict[str, Any]) -> ModelT:
        """Apply field updates to an existing record."""
        for field, value in updates.items():
            if hasattr(obj, field) and value is not None:
                setattr(obj, field, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        """Delete a record."""
        await self.session.delete(obj)
        await self.session.flush()

    async def save(self, obj: ModelT) -> ModelT:
        """Flush and refresh a record after modifications."""
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
