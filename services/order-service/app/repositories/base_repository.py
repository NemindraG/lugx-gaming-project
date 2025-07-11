"""
Base repository for Order Service.
Provides common data access patterns.
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

logger = structlog.get_logger()

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def create(self, **kwargs) -> T:
        """Create a new entity."""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
    
    async def find_by_id(self, id: UUID) -> Optional[T]:
        """Find entity by ID."""
        query = select(self.model).where(self.model.id == id)  # type: ignore
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all entities with pagination."""
        query = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Update an entity."""
        entity = await self.find_by_id(id)
        if entity:
            for key, value in kwargs.items():
                setattr(entity, key, value)
            await self.session.commit()
            await self.session.refresh(entity)
        return entity
    
    async def delete(self, id: UUID) -> bool:
        """Delete an entity."""
        query = delete(self.model).where(self.model.id == id)  # type: ignore
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
    
    async def count(self) -> int:
        """Count total entities."""
        query = select(func.count()).select_from(self.model)
        result = await self.session.scalar(query)
        return result or 0
    
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists."""
        query = select(1).where(self.model.id == id).limit(1)  # type: ignore
        result = await self.session.execute(query)
        return result.scalar() is not None