# src/repositories/CatalogItem_repository.py
from shared.database import Repository
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from ..models.catalog_item import CatalogItem
from ..models.enums import SyncStatus, AnalysisStatus

class CatalogItemRepository(Repository[CatalogItem]):
    """Repository for catalog CatalogItems"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(CatalogItem, session_factory)

    async def find_by_shop_and_variant(
        self, 
        shop_id: str, 
        product_id: str, 
        variant_id: str
    ) -> Optional[CatalogItem]:
        """Find CatalogItem by shop and variant IDs"""
        async for session in self._session():
            stmt = select(CatalogItem).where(
                and_(
                    CatalogItem.shop_id == shop_id,
                    CatalogItem.product_id == product_id,
                    CatalogItem.variant_id == variant_id
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
    ) -> List[CatalogItem]:
        """Find CatalogItems by shop with filters"""
        async for session in self._session():
            query = select(CatalogItem).where(CatalogItem.shop_id == shop_id)

            if category:
                query = query.where(CatalogItem.product_type == category)

            if status:
                query = query.where(CatalogItem.sync_status == status)
            
            if search:
                search_filter = or_(
                    CatalogItem.product_title.ilike(f"%{search}%"),
                    CatalogItem.variant_title.ilike(f"%{search}%"),
                    CatalogItem.variant_sku.ilike(f"%{search}%")
                )
                query = query.where(search_filter)

            query = query.order_by(CatalogItem.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            
            return list(result.scalars().all())
    
    async def count_by_shop_id(
        self,
        shop_id: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> int | None:
        """Count CatalogItems by shop with filters"""
        async for session in self._session():
            query = select(func.count(CatalogItem.id)).where(CatalogItem.shop_id == shop_id)
            
            if category:
                query = query.where(CatalogItem.product_type == category)
            
            if status:
                query = query.where(CatalogItem.sync_status == status)
            
            if search:
                search_filter = or_(
                    CatalogItem.product_title.ilike(f"%{search}%"),
                    CatalogItem.variant_title.ilike(f"%{search}%"),
                    CatalogItem.variant_sku.ilike(f"%{search}%")
                )
                query = query.where(search_filter)
            
            result = await session.execute(query)
            return result.scalar()
    
    async def find_pending_analysis(
        self, 
        shop_id: str, 
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[CatalogItem]:
        """Find CatalogItems needing analysis"""
        async for session in self._session():
            query = select(CatalogItem).where(
                and_(
                    CatalogItem.shop_id == shop_id,
                    CatalogItem.sync_status == SyncStatus.SYNCED,
                    CatalogItem.analysis_status == AnalysisStatus.PENDING
                )
            )
            
            if since:
                query = query.where(CatalogItem.synced_at >= since)
            
            query = query.limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def find_stuck_analysis(
        self, 
        cutoff_time: datetime,
        limit: int = 100
    ) -> List[CatalogItem]:
        """Find CatalogItems stuck in analysis"""
        async for session in self._session():
            query = select(CatalogItem).where(
                and_(
                    CatalogItem.analysis_status == AnalysisStatus.PENDING,
                    CatalogItem.synced_at < cutoff_time,
                    or_(
                        CatalogItem.requeued_at.is_(None),
                        CatalogItem.requeued_at < cutoff_time
                    )
                )
            ).limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())