# services/billing-service/src/repositories/subscription_repository.py
from shared.database import Repository
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List


class SubscriptionRepository(Repository[Subscription]):
    """Repository for subscription operations"""
    
    def __init__(self, session_factory):
        super().__init__(Subscription, session_factory)
    
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


class OneTimePurchaseRepository(Repository[OneTimePurchase]):
    """Repository for one-time purchase operations"""
    
    def __init__(self, session_factory):
        super().__init__(OneTimePurchase, session_factory)
    
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


class BillingPlanRepository(Repository[BillingPlan]):
    """Repository for billing plan operations"""
    
    def __init__(self, session_factory):
        super().__init__(BillingPlan, session_factory)
    
    async def find_active_plans(self) -> List[BillingPlan]:
        """Find all active plans ordered by sort_order"""
        async for session in self._session():
            stmt = select(self.model).where(
                self.model.is_active == True
            ).order_by(self.model.sort_order, self.model.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())


class TrialExtensionRepository(Repository[TrialExtension]):
    """Repository for trial extension operations"""
    
    def __init__(self, session_factory):
        super().__init__(TrialExtension, session_factory)
    
    async def find_by_merchant_id(self, merchant_id: UUID) -> List[TrialExtension]:
        """Find all extensions for merchant"""
        async for session in self._session():
            stmt = select(self.model).where(
                self.model.merchant_id == merchant_id
            ).order_by(self.model.created_at)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def count_by_merchant_id(self, merchant_id: UUID) -> int:
        """Count extensions for merchant"""
        async for session in self._session():
            stmt = select(self.model).where(
                self.model.merchant_id == merchant_id
            )
            result = await session.execute(stmt)
            return len(list(result.scalars().all()))
