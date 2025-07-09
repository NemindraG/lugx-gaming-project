"""
Base Repository Abstract Class
Provides common database operations for all repositories.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from uuid import UUID

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from app.models.game import Base

T = TypeVar('T', bound=Base)


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository providing common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def get_by_id(self, id: UUID, load_relationships: bool = True) -> Optional[T]:
        """Get entity by ID with optional relationship loading."""
        query = select(self.model).where(self.model.id == id)
        
        if load_relationships:
            query = self._apply_default_relationships(query)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_slug(self, slug: str, load_relationships: bool = True) -> Optional[T]:
        """Get entity by slug if model has slug field."""
        if not hasattr(self.model, 'slug'):
            raise NotImplementedError(f"{self.model.__name__} doesn't have slug field")
        
        query = select(self.model).where(self.model.slug == slug)
        
        if load_relationships:
            query = self._apply_default_relationships(query)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        limit: int = 100, 
        offset: int = 0,
        load_relationships: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """Get all entities with pagination and filtering."""
        query = select(self.model)
        
        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)
        
        # Apply ordering
        if order_by:
            query = self._apply_ordering(query, order_by)
        
        # Apply relationships
        if load_relationships:
            query = self._apply_default_relationships(query)
        
        # Apply pagination
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create(self, **kwargs) -> T:
        """Create a new entity."""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Update an entity by ID."""
        query = update(self.model).where(self.model.id == id).values(**kwargs)
        await self.session.execute(query)
        await self.session.flush()
        return await self.get_by_id(id)
    
    async def delete(self, id: UUID) -> bool:
        """Delete an entity by ID."""
        query = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.rowcount > 0
    
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists by ID."""
        query = select(self.model.id).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities with optional filters."""
        query = select(self.model).count()
        
        if filters:
            query = self._apply_filters(query, filters)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def search(
        self, 
        query_text: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[T]:
        """Search entities by text (override in subclasses)."""
        raise NotImplementedError("Search must be implemented in subclasses")
    
    def _apply_filters(self, query: Select, filters: Dict[str, Any]) -> Select:
        """Apply filters to query."""
        for field, value in filters.items():
            if hasattr(self.model, field):
                column = getattr(self.model, field)
                if isinstance(value, list):
                    query = query.where(column.in_(value))
                elif isinstance(value, dict):
                    # Handle range filters
                    if 'min' in value:
                        query = query.where(column >= value['min'])
                    if 'max' in value:
                        query = query.where(column <= value['max'])
                else:
                    query = query.where(column == value)
        return query
    
    def _apply_ordering(self, query: Select, order_by: str) -> Select:
        """Apply ordering to query."""
        if order_by.startswith('-'):
            # Descending order
            field = order_by[1:]
            if hasattr(self.model, field):
                query = query.order_by(getattr(self.model, field).desc())
        else:
            # Ascending order
            if hasattr(self.model, order_by):
                query = query.order_by(getattr(self.model, order_by))
        return query
    
    def _apply_default_relationships(self, query: Select) -> Select:
        """Apply default relationship loading (override in subclasses)."""
        return query
    
    async def bulk_create(self, entities: List[Dict[str, Any]]) -> List[T]:
        """Create multiple entities in bulk."""
        created_entities = []
        for entity_data in entities:
            entity = self.model(**entity_data)
            self.session.add(entity)
            created_entities.append(entity)
        
        await self.session.flush()
        return created_entities
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """Update multiple entities in bulk."""
        updated_count = 0
        for update_data in updates:
            entity_id = update_data.pop('id')
            query = update(self.model).where(self.model.id == entity_id).values(**update_data)
            result = await self.session.execute(query)
            updated_count += result.rowcount
        
        await self.session.flush()
        return updated_count
    
    async def bulk_delete(self, ids: List[UUID]) -> int:
        """Delete multiple entities in bulk."""
        query = delete(self.model).where(self.model.id.in_(ids))
        result = await self.session.execute(query)
        return result.rowcount