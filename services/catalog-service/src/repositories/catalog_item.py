# src/repositories/item_repository.py
from shared.database import Repository
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..models.item import Item
from ..models.enums import SyncStatus, AnalysisStatus

class ItemRepository(Repository[Item]):
    """Repository for catalog items"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(Item, session_factory)
    
    async def find_by_shop_and_variant(
        self, 
        shop_id: str, 
        product_id: str, 
        variant_id: str
    ) -> Optional[Item]:
        """Find item by shop and variant IDs"""
        async for session in self._session():
            stmt = select(Item).where(
                and_(
                    Item.shop_id == shop_id,
                    Item.product_id == product_id,
                    Item.variant_id == variant_id
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_by_shop_id(
        self, 
        shop_id: str, 
        limit: int = 50, 
        offset: int = 0,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Item]:
        """Find items by shop with filters"""
        async for session in self._session():
            query = select(Item).where(Item.shop_id == shop_id)
            
            if category:
                query = query.where(Item.product_type == category)
            
            if status:
                query = query.where(Item.sync_status == status)
            
            if search:
                search_filter = or_(
                    Item.product_title.ilike(f"%{search}%"),
                    Item.variant_title.ilike(f"%{search}%"),
                    Item.variant_sku.ilike(f"%{search}%")
                )
                query = query.where(search_filter)
            
            query = query.order_by(Item.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def count_by_shop_id(
        self,
        shop_id: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        """Count items by shop with filters"""
        async for session in self._session():
            query = select(func.count(Item.id)).where(Item.shop_id == shop_id)
            
            if category:
                query = query.where(Item.product_type == category)
            
            if status:
                query = query.where(Item.sync_status == status)
            
            if search:
                search_filter = or_(
                    Item.product_title.ilike(f"%{search}%"),
                    Item.variant_title.ilike(f"%{search}%"),
                    Item.variant_sku.ilike(f"%{search}%")
                )
                query = query.where(search_filter)
            
            result = await session.execute(query)
            return result.scalar()
    
    async def find_pending_analysis(
        self, 
        shop_id: str, 
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Item]:
        """Find items needing analysis"""
        async for session in self._session():
            query = select(Item).where(
                and_(
                    Item.shop_id == shop_id,
                    Item.sync_status == SyncStatus.SYNCED,
                    Item.analysis_status == AnalysisStatus.PENDING
                )
            )
            
            if since:
                query = query.where(Item.synced_at >= since)
            
            query = query.limit(limit)
            result = await session.execute(query)
            return result.scalars().all()
    
    async def find_stuck_analysis(
        self, 
        cutoff_time: datetime,
        limit: int = 100
    ) -> List[Item]:
        """Find items stuck in analysis"""
        async for session in self._session():
            query = select(Item).where(
                and_(
                    Item.analysis_status == AnalysisStatus.PENDING,
                    Item.synced_at < cutoff_time,
                    or_(
                        Item.requeued_at.is_(None),
                        Item.requeued_at < cutoff_time
                    )
                )
            ).limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all()