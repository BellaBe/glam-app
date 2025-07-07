
# services/scheduler-service/src/repositories/base.py
"""Base repository with common functionality"""

from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from shared.database.session import DatabaseSessionManager

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType], db_manager: DatabaseSessionManager):
        self.model = model
        self.db_manager = db_manager
    
    async def _session(self):
        """Get database session"""
        async with self.db_manager.get_session() as session:
            yield session
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get entity by ID"""
        async for session in self._session():
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
    
    async def get_all(
        self,
        offset: int = 0,
        limit: int = 100,
        filters: Optional[List[Any]] = None
    ) -> List[ModelType]:
        """Get all entities with pagination"""
        async for session in self._session():
            query = select(self.model)
            
            if filters:
                query = query.where(and_(*filters))
            
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def count(self, filters: Optional[List[Any]] = None) -> int:
        """Count entities"""
        async for session in self._session():
            query = select(func.count()).select_from(self.model)
            
            if filters:
                query = query.where(and_(*filters))
            
            result = await session.execute(query)
            return result.scalar() or 0
    
    async def create(self, entity: ModelType) -> ModelType:
        """Create entity"""
        async for session in self._session():
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity
    
    async def update(self, entity: ModelType) -> ModelType:
        """Update entity"""
        async for session in self._session():
            await session.merge(entity)
            await session.commit()
            await session.refresh(entity)
            return entity
    
    async def delete(self, id: UUID) -> bool:
        """Delete entity"""
        async for session in self._session():
            entity = await self.get_by_id(id)
            if entity:
                await session.delete(entity)
                await session.commit()
                return True
            return False
