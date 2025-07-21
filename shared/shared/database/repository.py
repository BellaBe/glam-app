# glam-app/shared/database/repository.py
from sqlalchemy import select
from typing import TypeVar, Generic, Type, AsyncIterator
from uuid import UUID
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from .base import Base

T = TypeVar("T", bound=Base)


class Repository(Generic[T]):
    """
    Generic repository providing basic CRUD operations.
    Services can extend this for specific domain needs.
    """
    
    def __init__(self, model: Type[T], session_factory: async_sessionmaker[AsyncSession]):
        self.model = model
        self.session_factory = session_factory

    # helper used by child methods
    async def _session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session

    async def save(self, instance: T) -> T | None:
        """Save an instance to the database"""
        async for session in self._session():
            session.add(instance)
            await session.commit()
            return instance
    
    async def update(self, instance: T) -> T | None:
        """Update an existing instance"""
        async for session in self._session():
            await session.merge(instance)
            await session.commit()
            return instance
        
    async def delete(self, instance: T) -> None:
        """Delete an instance from the database"""
        async for session in self._session():
            await session.delete(instance)
            await session.commit()
    
    async def delete_by_id(self, id: str | UUID) -> None:
        """Delete an instance by its ID"""
        async for session in self._session():
            instance = await session.get(self.model, id)
            if instance:
                await session.delete(instance)
                await session.commit()
        
    async def find_by_id(self, id: str | UUID) -> T | None:
        """Find an instance by its ID"""
        async for session in self._session():
            result = await session.get(self.model, id)
            return result
        
    async def find_all(
        self,
        * ,
        limit: int | None = None,
        offset: int | None = None,
        **filters
    ) -> list[T] | None:
        """
        Return a list of model instances.
        Optional keyword filters map column names to values (exact match).
        You can also page results with limit/offset.
        """
        async for session in self._session():
            stmt = select(self.model)

            # Apply column == value filters
            for col, val in filters.items():
                try:
                    stmt = stmt.where(getattr(self.model, col) == val)
                except AttributeError:
                    raise ValueError(f"{col!r} is not a valid column on {self.model.__name__}")

            # Pagination
            if offset is not None:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            return list(result.scalars().all())
