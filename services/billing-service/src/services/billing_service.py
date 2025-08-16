
from uuid import UUID
from typing import Optional
from datetime import datetime
import redis.asyncio as redis
from shared.utils.logger import ServiceLogger
from shared.utils.idempotency_key import generate_idempotency_key
from ..config import ServiceConfig
from ..repositories.billing_repository import BillingRepository
from ..repositories.purchase_repository import PurchaseRepository
from ..schemas.billing import (
    TrialStatusOut, TrialActivatedOut, BillingStatusOut,
    TrialStartedPayload
)
from ..exceptions import MerchantNotFoundError, TrialAlreadyUsedError
from ..events.publishers import BillingEventPublisher


class BillingService:
    """Service for billing operations"""
    
    def __init__(
        self,
        config: ServiceConfig,
        billing_repo: BillingRepository,
        purchase_repo: PurchaseRepository,
        publisher: BillingEventPublisher,
        redis_client: redis.Redis,
        logger: ServiceLogger
    ):
        self.config = config
        self.billing_repo = billing_repo
        self.purchase_repo = purchase_repo
        self.publisher = publisher
        self.redis = redis_client
        self.logger = logger
    
    async def create_billing_record(self, merchant_id: UUID) -> None:
        """Create billing record for new merchant"""
        try:
            existing = await self.billing_repo.find_by_merchant_id(merchant_id)
            if existing:
                self.logger.info(f"Billing record already exists for merchant {merchant_id}")
                return
            
            await self.billing_repo.create(merchant_id)
            self.logger.info(f"Created billing record for merchant {merchant_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to create billing record: {e}")
            raise
    
    async def get_trial_status(self, merchant_id: UUID) -> TrialStatusOut:
        """Get trial status for merchant"""
        record = await self.billing_repo.find_by_merchant_id(merchant_id)
        if not record:
            raise MerchantNotFoundError(str(merchant_id))
        
        # Determine if trial is active
        active = (
            not record.trial_available and
            record.trial_started_at is not None and
            record.trial_ends_at is not None and
            record.trial_ends_at > datetime.utcnow()
        )
        
        return TrialStatusOut(
            available=record.trial_available,
            active=active,
            started_at=record.trial_started_at,
            ends_at=record.trial_ends_at
        )
    
    async def activate_trial(
        self,
        merchant_id: UUID,
        idempotency_key: Optional[str] = None
    ) -> TrialActivatedOut:
        """Activate trial for merchant"""
        # Check idempotency
        if idempotency_key:
            cache_key = f"trial:{idempotency_key}"
            cached = await self.redis.get(cache_key)
            if cached:
                import json
                return TrialActivatedOut(**json.loads(cached))
        
        # Get billing record
        record = await self.billing_repo.find_by_merchant_id(merchant_id)
        if not record:
            raise MerchantNotFoundError(str(merchant_id))
        
        # Check if trial already used
        if not record.trial_available:
            raise TrialAlreadyUsedError(str(merchant_id))
        
        # Activate trial
        updated = await self.billing_repo.activate_trial(
            merchant_id,
            self.config.trial_duration_days
        )
        
        # Publish event
        await self.publisher.trial_started(
            TrialStartedPayload(
                merchant_id=merchant_id,
                ends_at=updated.trial_ends_at,
                credits=self.config.trial_credits
            )
        )
        
        # Create response
        response = TrialActivatedOut(
            success=True,
            ends_at=updated.trial_ends_at,
            credits_granted=self.config.trial_credits
        )
        
        # Cache for idempotency
        if idempotency_key:
            cache_key = f"trial:{idempotency_key}"
            await self.redis.setex(
                cache_key,
                86400,  # 24 hours
                response.model_dump_json()
            )
        
        return response
    
    async def get_billing_status(self, merchant_id: UUID) -> BillingStatusOut:
        """Get overall billing status"""
        record = await self.billing_repo.find_by_merchant_id(merchant_id)
        if not record:
            raise MerchantNotFoundError(str(merchant_id))
        
        # Get trial status
        trial = await self.get_trial_status(merchant_id)
        
        # Get recent purchases
        purchases = await self.purchase_repo.find_by_merchant(merchant_id, limit=5)
        
        return BillingStatusOut(
            trial=trial,
            credits_purchased=record.total_credits_purchased,
            last_purchase_at=record.last_purchase_at,
            recent_purchases=purchases
        )
    
    async def check_expired_trials(self) -> None:
        """Check and process expired trials (cron job)"""
        expired_records = await self.billing_repo.find_expired_trials()
        
        for record in expired_records:
            try:
                await self.publisher.trial_expired({
                    "merchant_id": UUID(record.merchant_id),
                    "expired_at": record.trial_ends_at
                })
                
                self.logger.info(f"Published trial expired event for merchant {record.merchant_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to process expired trial: {e}")


