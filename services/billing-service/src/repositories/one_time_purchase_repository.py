from typing import Optional, List
from uuid import UUID
from prisma import Prisma
from prisma.models import OneTimePurchase

class OneTimePurchaseRepository:
    """Repository for OneTimePurchase operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def find_by_charge_id(self, charge_id: str) -> Optional[OneTimePurchase]:
        """Find one-time purchase by charge ID"""
        return await self.prisma.onetimepurchase.find_unique(
            where={"chargeId": charge_id}
        )
    
    async def find_by_webhook_id(self, webhook_id: str) -> Optional[OneTimePurchase]:
        """Find one-time purchase by webhook ID for deduplication"""
        return await self.prisma.onetimepurchase.find_unique(
            where={"lastWebhookId": webhook_id}
        )
    
    async def create(
        self,
        shop_domain: str,
        charge_id: str,
        status: str,
        is_test: bool = False,
        credits: Optional[int] = None,
        managed_plan_id: Optional[str] = None,
        webhook_id: Optional[str] = None
    ) -> OneTimePurchase:
        """Create new one-time purchase record"""
        return await self.prisma.onetimepurchase.create(
            data={
                "shopDomain": shop_domain,
                "chargeId": charge_id,
                "status": status,
                "isTest": is_test,
                "credits": credits,
                "managedPlanId": managed_plan_id,
                "lastWebhookId": webhook_id
            }
        )
    
    async def update_status(
        self,
        charge_id: str,
        status: str,
        webhook_id: Optional[str] = None
    ) -> OneTimePurchase:
        """Update one-time purchase status"""
        update_data = {"status": status}
        if webhook_id:
            update_data["lastWebhookId"] = webhook_id
        
        return await self.prisma.onetimepurchase.update(
            where={"chargeId": charge_id},
            data=update_data
        )
    
    async def find_by_shop_domain(self, shop_domain: str) -> List[OneTimePurchase]:
        """Find all one-time purchases for a shop"""
        return await self.prisma.onetimepurchase.find_many(
            where={"shopDomain": shop_domain},
            order_by={"updatedAt": "desc"}
        )

