from datetime import datetime, timedelta
from uuid import UUID

from prisma import Prisma  # type: ignore[attr-defined]
from prisma.models import BillingRecord

from shared.utils.logger import ServiceLogger


class BillingRepository:
    """Repository for billing record operations"""

    def __init__(self, prisma: Prisma, logger: ServiceLogger):
        self.prisma = prisma
        self.logger = logger

    async def create(self, merchant_id: UUID) -> BillingRecord:
        """Create new billing record"""
        return await self.prisma.billingrecord.create(
            data={"merchant_id": str(merchant_id), "trial_available": True, "total_credits_purchased": 0}
        )

    async def find_by_merchant_id(self, merchant_id: UUID) -> BillingRecord | None:
        """Find billing record by merchant ID"""
        return await self.prisma.billingrecord.find_unique(where={"merchant_id": str(merchant_id)})

    async def activate_trial(self, merchant_id: UUID, duration_days: int = 14) -> BillingRecord:
        """Activate trial for merchant"""
        now = datetime.utcnow()
        ends_at = now + timedelta(days=duration_days)

        return await self.prisma.billingrecord.update(
            where={"merchant_id": str(merchant_id)},
            data={"trial_available": False, "trial_started_at": now, "trial_ends_at": ends_at},
        )

    async def update_purchase_totals(self, merchant_id: UUID, credits: int) -> BillingRecord:
        """Update purchase totals after successful purchase"""
        return await self.prisma.billingrecord.update(
            where={"merchant_id": str(merchant_id)},
            data={"total_credits_purchased": {"increment": credits}, "last_purchase_at": datetime.utcnow()},
        )

    async def find_expired_trials(self) -> list[BillingRecord]:
        """Find all expired trials that haven't been processed"""
        return await self.prisma.billingrecord.find_many(
            where={
                "trial_ends_at": {"lte": datetime.utcnow()},
                "trial_available": False,
                "trial_started_at": {"not": None},
            }
        )
