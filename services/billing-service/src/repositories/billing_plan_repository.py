from typing import Optional, List
from uuid import UUID
from prisma import Prisma
from prisma.models import BillingPlan
from ..schemas.billing import BillingPlanOut

class BillingPlanRepository:
    """Repository for BillingPlan operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def find_active_plans(self) -> List[BillingPlanOut]:
        """Find all active billing plans sorted by sortOrder"""
        plans = await self.prisma.billingplan.find_many(
            where={"active": True},
            order_by={"sortOrder": "asc"}
        )
        return [BillingPlanOut.model_validate(plan) for plan in plans]
    
    async def find_by_id(self, plan_id: str) -> Optional[BillingPlanOut]:
        """Find billing plan by ID"""
        plan = await self.prisma.billingplan.find_unique(
            where={"id": plan_id}
        )
        return BillingPlanOut.model_validate(plan) if plan else None
    
    async def find_by_shopify_handle(self, handle: str) -> Optional[BillingPlanOut]:
        """Find billing plan by Shopify handle"""
        plan = await self.prisma.billingplan.find_unique(
            where={"shopifyHandle": handle}
        )
        return BillingPlanOut.model_validate(plan) if plan else None

