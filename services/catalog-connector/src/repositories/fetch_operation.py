# src/repositories/fetch_operation_repository.py
from shared.database import Repository
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..models.fetch_operation import FetchOperation

class FetchOperationRepository(Repository[FetchOperation]):
    """Repository for fetch operations"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(FetchOperation, session_factory)
    
    async def find_by_sync_id(self, sync_id: UUID) -> Optional[FetchOperation]:
        """Find fetch operation by sync ID"""
        async for session in self._session():
            stmt = select(FetchOperation).where(FetchOperation.sync_id == sync_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_active_operations(self) -> List[FetchOperation]:
        """Find operations that are still active"""
        async for session in self._session():
            stmt = select(FetchOperation).where(
                FetchOperation.status.in_(["started", "processing"])
            )
            result = await session.execute(stmt)
            return result.scalars().all()