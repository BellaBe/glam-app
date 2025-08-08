from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from prisma import Prisma
from prisma.models import MerchantTrial
from prisma.enums import TrialStatus

class MerchantTrialRepository:
    """Repository for MerchantTrial operations using Prisma"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def find_by_shop_domain(self, shop_domain: str) -> Optional[MerchantTrial]:
        """Find merchant trial by shop domain"""
        return await self.prisma.merchanttrial.find_unique(
            where={"shopDomain": shop_domain}
        )
    
    async def create(self, shop_domain: str, days: int) -> MerchantTrial:
        """Create new trial for merchant"""
        now = datetime.utcnow()
        ends_at = now + timedelta(days=days)
        
        return await self.prisma.merchanttrial.create(
            data={
                "shopDomain": shop_domain,
                "status": TrialStatus.active,
                "days": days,
                "startedAt": now,
                "endsAt": ends_at,
                "consumed": False,
                "trialStartedBy": "user_action"
            }
        )
    
    async def activate_existing(self, trial_id: str) -> MerchantTrial:
        """Activate an existing never_started trial"""
        trial = await self.prisma.merchanttrial.find_unique(
            where={"id": trial_id}
        )
        
        if not trial:
            raise ValueError(f"Trial {trial_id} not found")
        
        now = datetime.utcnow()
        ends_at = now + timedelta(days=trial.days)
        
        return await self.prisma.merchanttrial.update(
            where={"id": trial_id},
            data={
                "status": TrialStatus.active,
                "startedAt": now,
                "endsAt": ends_at,
                "trialStartedBy": "user_action"
            }
        )
    
    async def expire_trial(self, trial_id: str) -> MerchantTrial:
        """Mark trial as expired"""
        return await self.prisma.merchanttrial.update(
            where={"id": trial_id},
            data={
                "status": TrialStatus.expired,
                "consumed": True
            }
        )
    
    async def extend_trial(self, shop_domain: str, additional_days: int) -> MerchantTrial:
        """Extend an active trial"""
        trial = await self.find_by_shop_domain(shop_domain)
        
        if not trial or trial.status != TrialStatus.active:
            raise ValueError(f"No active trial found for {shop_domain}")
        
        new_ends_at = trial.endsAt + timedelta(days=additional_days)
        
        return await self.prisma.merchanttrial.update(
            where={"id": trial.id},
            data={"endsAt": new_ends_at}
        )
    
    async def find_expired_trials(self) -> List[MerchantTrial]:
        """Find all trials that should be expired"""
        now = datetime.utcnow()
        
        return await self.prisma.merchanttrial.find_many(
            where={
                "status": TrialStatus.active,
                "endsAt": {"lte": now},
                "consumed": False
            }
        )
    
    async def count_active_trials(self) -> int:
        """Count currently active trials"""
        return await self.prisma.merchanttrial.count(
            where={"status": TrialStatus.active}
        )

