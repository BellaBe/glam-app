# glam-app/shared/database/repository.py
from typing import TypeVar, Generic, Type, AsyncIterator
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