# src/repositories/sync_operation_repository.py
from shared.database import Repository
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..models.sync_operation import SyncOperation
from ..models.enums import SyncOperationStatus

class SyncOperationRepository(Repository[SyncOperation]):
    """Repository for sync operations"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(SyncOperation, session_factory)
    
    async def find_by_shop_id(
        self, 
        shop_id: str, 
        limit: int = 10
    ) -> List[SyncOperation]:
        """Find sync operations by shop"""
        async for session in self._session():
            stmt = select(SyncOperation).where(
                SyncOperation.shop_id == shop_id
            ).order_by(desc(SyncOperation.started_at)).limit(limit)
            
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def find_running_for_shop(self, shop_id: str) -> Optional[SyncOperation]:
        """Find running sync for shop"""
        async for session in self._session():
            stmt = select(SyncOperation).where(
                and_(
                    SyncOperation.shop_id == shop_id,
                    SyncOperation.status == SyncOperationStatus.RUNNING
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_last_completed(self, shop_id: str) -> Optional[SyncOperation]:
        """Find last completed sync for incremental sync timestamp"""
        async for session in self._session():
            stmt = select(SyncOperation).where(
                and_(
                    SyncOperation.shop_id == shop_id,
                    SyncOperation.status == SyncOperationStatus.COMPLETED
                )
            ).order_by(desc(SyncOperation.completed_at)).limit(1)
            
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_incomplete_operations(
        self, 
        cutoff_time: datetime,
        limit: int = 1000
    ) -> List[SyncOperation]:
        """Find incomplete sync operations for recovery"""
        async for session in self._session():
            stmt = select(SyncOperation).where(
                and_(
                    SyncOperation.status == SyncOperationStatus.RUNNING,
                    SyncOperation.started_at < cutoff_time
                )
            ).limit(limit)
            
            result = await session.execute(stmt)
            return result.scalars().all()

# src/repositories/analysis_result_repository.py
from shared.database import Repository
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional
from uuid import UUID
from ..models.analysis_result import AnalysisResult

class AnalysisResultRepository(Repository[AnalysisResult]):
    """Repository for analysis results"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(AnalysisResult, session_factory)
    
    async def find_by_item_and_version(
        self, 
        item_id: UUID, 
        model_version: str
    ) -> Optional[AnalysisResult]:
        """Find analysis result by item and model version"""
        async for session in self._session():
            stmt = select(AnalysisResult).where(
                and_(
                    AnalysisResult.item_id == item_id,
                    AnalysisResult.model_version == model_version
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_by_item_id(self, item_id: UUID) -> Optional[AnalysisResult]:
        """Find latest analysis result for item"""
        async for session in self._session():
            stmt = select(AnalysisResult).where(
                AnalysisResult.item_id == item_id
            ).order_by(AnalysisResult.analyzed_at.desc()).limit(1)
            
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
