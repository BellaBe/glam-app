# src/repositories/fetch_operation_repository.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database import Repository

from ..models.fetch_operation import FetchOperation


class FetchOperationRepository(Repository[FetchOperation]):
    """Repository for fetch operations"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(FetchOperation, session_factory)

    async def find_by_sync_id(self, sync_id: UUID) -> FetchOperation | None:
        """Find fetch operation by sync ID"""
        async for session in self._session():
            stmt = select(FetchOperation).where(FetchOperation.sync_id == sync_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def find_active_operations(self) -> list[FetchOperation]:
        """Find operations that are still active"""
        async for session in self._session():
            stmt = select(FetchOperation).where(FetchOperation.status.in_(["started", "processing"]))
            result = await session.execute(stmt)
            return result.scalars().all()
