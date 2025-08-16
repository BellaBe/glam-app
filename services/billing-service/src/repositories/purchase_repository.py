
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from prisma import Prisma
from prisma.models import CreditPurchase
from prisma.enums import PurchaseStatus
from shared.utils.logger import ServiceLogger


class PurchaseRepository:
    """Repository for credit purchase operations"""
    
    def __init__(self, prisma: Prisma, logger: ServiceLogger):
        self.prisma = prisma
        self.logger = logger
    
    async def create(
        self,
        merchant_id: UUID,
        credits: int,
        amount: str,
        platform: str,
        expiry_hours: int = 24
    ) -> CreditPurchase:
        """Create new purchase record"""
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        return await self.prisma.creditpurchase.create(
            data={
                "merchant_id": str(merchant_id),
                "credits": credits,
                "amount": amount,
                "status": PurchaseStatus.pending,
                "platform": platform,
                "expires_at": expires_at
            }
        )
    
    async def find_by_id(self, purchase_id: UUID) -> Optional[CreditPurchase]:
        """Find purchase by ID"""
        return await self.prisma.creditpurchase.find_unique(
            where={"id": str(purchase_id)}
        )
    
    async def find_by_charge_id(self, charge_id: str) -> Optional[CreditPurchase]:
        """Find purchase by platform charge ID"""
        return await self.prisma.creditpurchase.find_unique(
            where={"platform_charge_id": charge_id}
        )
    
    async def find_by_merchant(
        self,
        merchant_id: UUID,
        limit: int = 10
    ) -> List[CreditPurchase]:
        """Find purchases for merchant"""
        return await self.prisma.creditpurchase.find_many(
            where={"merchant_id": str(merchant_id)},
            order_by={"created_at": "desc"},
            take=limit
        )
    
    async def update_platform_charge_id(
        self,
        purchase_id: UUID,
        charge_id: str
    ) -> CreditPurchase:
        """Update platform charge ID"""
        return await self.prisma.creditpurchase.update(
            where={"id": str(purchase_id)},
            data={"platform_charge_id": charge_id}
        )
    
    async def complete_purchase(
        self,
        purchase_id: UUID
    ) -> CreditPurchase:
        """Mark purchase as completed"""
        return await self.prisma.creditpurchase.update(
            where={"id": str(purchase_id)},
            data={
                "status": PurchaseStatus.completed,
                "completed_at": datetime.utcnow()
            }
        )
    
    async def fail_purchase(
        self,
        purchase_id: UUID
    ) -> CreditPurchase:
        """Mark purchase as failed"""
        return await self.prisma.creditpurchase.update(
            where={"id": str(purchase_id)},
            data={"status": PurchaseStatus.failed}
        )
    
    async def expire_pending_purchases(self) -> int:
        """Expire all pending purchases past expiry time"""
        result = await self.prisma.creditpurchase.update_many(
            where={
                "status": PurchaseStatus.pending,
                "expires_at": {"lte": datetime.utcnow()}
            },
            data={"status": PurchaseStatus.expired}
        )
        return result


