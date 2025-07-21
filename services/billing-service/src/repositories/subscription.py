# services/billing-service/src/repositories/subscription_repository.py
from shared.database import Repository
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List

from ..models import Subscription, SubscriptionStatus
from uuid import UUID


class SubscriptionRepository(Repository[Subscription]):
    """Repository for subscription operations"""
    
    def __init__(self,
                model_class: type[Subscription],
                session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(model_class, session_factory)

    async def find_by_shopify_id(self, shopify_subscription_id: str) -> Optional[Subscription]:
        """Find subscription by Shopify ID"""
        async for session in self._session():
            stmt = select(self.model).where(
                self.model.shopify_subscription_id == shopify_subscription_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_active_by_merchant(self, merchant_id: UUID) -> Optional[Subscription]:
        """Find active subscription for merchant"""
        async for session in self._session():
            stmt = select(self.model).where(
                and_(
                    self.model.merchant_id == merchant_id,
                    self.model.status == SubscriptionStatus.ACTIVE
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_by_merchant(self, merchant_id: UUID) -> List[Subscription]:
        """Find all subscriptions for merchant"""
        async for session in self._session():
            stmt = select(self.model).where(
                self.model.merchant_id == merchant_id
            ).order_by(self.model.created_at.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
        return []
