from typing import Optional, Dict, Any
from datetime import datetime
import redis.asyncio as redis
from shared.utils.logger import ServiceLogger
from ..config import ServiceConfig
from ..repositories.merchant_billing_repository import MerchantBillingRepository
from ..repositories.one_time_purchase_repository import OneTimePurchaseRepository
from ..schemas.billing import (
    AppSubscriptionUpdatedPayload,
    AppPurchaseUpdatedPayload,
    AppUninstalledPayload,
    SubscriptionStatus
)
from .billing_service import BillingService

class WebhookProcessingService:
    """Service for processing Shopify webhooks"""
    
    def __init__(
        self,
        config: ServiceConfig,
        billing_repo: MerchantBillingRepository,
        purchase_repo: OneTimePurchaseRepository,
        billing_service: BillingService,
        redis_client: redis.Redis,
        logger: ServiceLogger,
    ):
        self.config = config
        self.billing_repo = billing_repo
        self.purchase_repo = purchase_repo
        self.billing_service = billing_service
        self.redis = redis_client
        self.logger = logger
    
    def map_shopify_status(self, status: str) -> SubscriptionStatus:
        """Map Shopify subscription status to our enum"""
        status_map = {
            "ACTIVE": SubscriptionStatus.active,
            "PENDING": SubscriptionStatus.pending,
            "CANCELLED": SubscriptionStatus.cancelled,
            "EXPIRED": SubscriptionStatus.expired,
            "FROZEN": SubscriptionStatus.paused,
            "PAUSED": SubscriptionStatus.paused,
        }
        return status_map.get(status.upper(), SubscriptionStatus.none)
    
    async def process_subscription_updated(
        self, 
        payload: AppSubscriptionUpdatedPayload
    ) -> Optional[Dict[str, Any]]:
        """Process subscription updated webhook"""
        shop_domain = self.billing_service.normalize_shop_domain(payload.shop_domain)
        
        # Check Redis dedupe first (fast path)
        dedupe_key = f"webhook:{payload.webhook_id}"
        if await self.redis.exists(dedupe_key):
            self.logger.info(
                "Webhook already processed (Redis)",
                extra={"webhook_id": payload.webhook_id}
            )
            return None
        
        # Set Redis key with 1 hour TTL
        await self.redis.setex(dedupe_key, 3600, "1")
        
        # Check DB dedupe (authoritative)
        existing = await self.billing_repo.find_by_webhook_id(payload.webhook_id)
        if existing:
            self.logger.info(
                "Webhook already processed (DB)",
                extra={"webhook_id": payload.webhook_id}
            )
            return None
        
        # Map status
        status = self.map_shopify_status(payload.status)
        
        # Update billing record
        billing = await self.billing_repo.update_subscription_status(
            shop_domain=shop_domain,
            status=status,
            external_id=payload.subscription_id,
            plan_handle=payload.plan_handle,
            current_period_end=payload.current_period_end,
            webhook_id=payload.webhook_id
        )
        
        # Clear entitlements cache
        await self.redis.delete(f"entitlements:{shop_domain}")
        
        return {
            "shop_domain": shop_domain,
            "status": status,
            "plan_handle": payload.plan_handle,
            "current_period_end": payload.current_period_end
        }
    
    async def process_purchase_updated(
        self,
        payload: AppPurchaseUpdatedPayload
    ) -> Optional[Dict[str, Any]]:
        """Process one-time purchase webhook"""
        shop_domain = self.billing_service.normalize_shop_domain(payload.shop_domain)
        
        # Check Redis dedupe
        dedupe_key = f"webhook:{payload.webhook_id}"
        if await self.redis.exists(dedupe_key):
            return None
        
        await self.redis.setex(dedupe_key, 3600, "1")
        
        # Check DB dedupe
        existing = await self.purchase_repo.find_by_webhook_id(payload.webhook_id)
        if existing:
            return None
        
        # Check if purchase exists
        purchase = await self.purchase_repo.find_by_charge_id(payload.charge_id)
        
        if purchase:
            # Update existing
            purchase = await self.purchase_repo.update_status(
                charge_id=payload.charge_id,
                status=payload.status,
                webhook_id=payload.webhook_id
            )
        else:
            # Create new
            purchase = await self.purchase_repo.create(
                shop_domain=shop_domain,
                charge_id=payload.charge_id,
                status=payload.status,
                is_test=payload.test,
                credits=payload.credits,
                webhook_id=payload.webhook_id
            )
        
        # Return data for event publishing
        if payload.status == "active" and payload.credits:
            return {
                "shop_domain": shop_domain,
                "credits": payload.credits,
                "charge_id": payload.charge_id
            }
        
        return None
    
    async def process_app_uninstalled(
        self,
        payload: AppUninstalledPayload
    ) -> None:
        """Process app uninstalled webhook"""
        shop_domain = self.billing_service.normalize_shop_domain(payload.shop_domain)
        
        # Update subscription status to cancelled
        billing = await self.billing_repo.find_by_shop_domain(shop_domain)
        if billing and billing.subscriptionStatus == SubscriptionStatus.active:
            await self.billing_repo.update_subscription_status(
                shop_domain=shop_domain,
                status=SubscriptionStatus.cancelled,
                webhook_id=payload.webhook_id
            )
            
            # Clear entitlements cache
            await self.redis.delete(f"entitlements:{shop_domain}")

