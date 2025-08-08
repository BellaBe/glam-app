from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from prisma import Prisma
from prisma.models import MerchantBilling
from prisma.enums import SubscriptionStatus

class MerchantBillingRepository:
    """Repository for MerchantBilling operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def find_by_shop_domain(self, shop_domain: str) -> Optional[MerchantBilling]:
        """Find merchant billing by shop domain"""
        return await self.prisma.merchantbilling.find_unique(
            where={"shopDomain": shop_domain}
        )
    
    async def find_by_webhook_id(self, webhook_id: str) -> Optional[MerchantBilling]:
        """Find merchant billing by webhook ID for deduplication"""
        return await self.prisma.merchantbilling.find_unique(
            where={"lastWebhookId": webhook_id}
        )
    
    async def upsert(self, shop_domain: str, data: Dict[str, Any]) -> MerchantBilling:
        """Upsert merchant billing record"""
        return await self.prisma.merchantbilling.upsert(
            where={"shopDomain": shop_domain},
            create={
                "shopDomain": shop_domain,
                **data
            },
            update=data
        )
    
    async def update_subscription_status(
        self, 
        shop_domain: str, 
        status: SubscriptionStatus,
        external_id: Optional[str] = None,
        plan_handle: Optional[str] = None,
        current_period_end: Optional[datetime] = None,
        webhook_id: Optional[str] = None
    ) -> MerchantBilling:
        """Update subscription status for merchant"""
        update_data = {
            "subscriptionStatus": status,
            "lastWebhookAt": datetime.utcnow()
        }
        
        if external_id is not None:
            update_data["externalId"] = external_id
        if plan_handle is not None:
            update_data["managedPlanHandle"] = plan_handle
        if current_period_end is not None:
            update_data["currentPeriodEnd"] = current_period_end
        if webhook_id is not None:
            update_data["lastWebhookId"] = webhook_id
        
        return await self.upsert(shop_domain, update_data)
    
    async def count_active_subscriptions_by_plan(self) -> Dict[str, int]:
        """Count active subscriptions grouped by plan"""
        result = await self.prisma.merchantbilling.group_by(
            by=["managedPlanHandle"],
            where={"subscriptionStatus": SubscriptionStatus.active},
            count=True
        )
        return {item["managedPlanHandle"]: item["_count"] for item in result}

