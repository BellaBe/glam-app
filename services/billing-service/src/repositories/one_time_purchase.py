# services/billing-service/src/repositories/one_time_purchase_repository.py
from shared.database import Repository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List

from ..models import OneTimePurchase
from uuid import UUID


class OneTimePurchaseRepository(Repository[OneTimePurchase]):
    """Repository for one-time purchase operations"""
    
    def __init__(self, 
                model_class: type[OneTimePurchase],
                session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(model_class, session_factory)

    async def find_by_shopify_id(self, shopify_charge_id: str) -> Optional[OneTimePurchase]:
        """Find purchase by Shopify charge ID"""
        async for session in self._session():
            stmt = select(self.model).where(
                self.model.shopify_charge_id == shopify_charge_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_by_merchant(self, merchant_id: UUID) -> List[OneTimePurchase]:
        """Find all purchases for merchant"""
        async for session in self._session():
            stmt = select(self.model).where(
                self.model.merchant_id == merchant_id
            ).order_by(self.model.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
        return []
