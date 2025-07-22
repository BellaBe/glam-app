# src/repositories/bulk_operation_repository.py
from shared.database import Repository
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..models.bulk_operation import BulkOperation, BulkOperationStatus

class BulkOperationRepository(Repository[BulkOperation]):
    """Repository for bulk operations"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(BulkOperation, session_factory)
    
    async def find_by_shopify_id(self, shopify_bulk_id: str) -> Optional[BulkOperation]:
        """Find bulk operation by Shopify ID"""
        async for session in self._session():
            stmt = select(BulkOperation).where(BulkOperation.shopify_bulk_id == shopify_bulk_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_by_sync_id(self, sync_id: UUID) -> Optional[BulkOperation]:
        """Find bulk operation by sync ID"""
        async for session in self._session():
            stmt = select(BulkOperation).where(BulkOperation.sync_id == sync_id).order_by(desc(BulkOperation.created_at))
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_running_operations(self, cutoff_time: datetime) -> List[BulkOperation]:
        """Find operations that should be polled"""
        async for session in self._session():
            stmt = select(BulkOperation).where(
                and_(
                    BulkOperation.status.in_([
                        BulkOperationStatus.CREATED,
                        BulkOperationStatus.RUNNING
                    ]),
                    BulkOperation.started_at < cutoff_time
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()