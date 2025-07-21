# services/billing-service/src/services/billing_service.py
"""Main billing service for subscription and payment management."""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID
import redis.asyncio as redis

from shared.utils.logger import ServiceLogger

from ..config import BillingServiceConfig
from ..events import BillingEventPublisher
from ..external import ShopifyBillingClient
from ..exceptions import (
    BillingPlanNotFoundError,
    SubscriptionNotFoundError,
    ConflictError,
)
from ..mappers.billing_plan import BillingPlanMapper
from ..mappers.subscription import SubscriptionMapper
from ..models import BillingInterval, SubscriptionStatus, Subscription
from ..repositories import BillingPlanRepository, SubscriptionRepository
from ..schemas.billing_plan import BillingPlanOut, BillingPlanIn, BillingPlanPatch
from ..schemas import (
    SubscriptionOut,
    SubscriptionCreateOut, 
)


class BillingService:
    """Main billing service for subscription and payment management"""

    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        plan_repo: BillingPlanRepository,
        shopify_client: ShopifyBillingClient,
        event_publisher: BillingEventPublisher,
        billing_mapper: BillingPlanMapper,
        subscription_mapper: SubscriptionMapper,
        redis_client: redis.Redis,
        logger: ServiceLogger,
        config: BillingServiceConfig,
    ):
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.shopify_client = shopify_client
        self.event_publisher = event_publisher
        self.billing_mapper = billing_mapper
        self.subscription_mapper = subscription_mapper
        self.redis_client = redis_client
        self.logger = logger
        self.config = config
        
    
    async def create_plan(self, plan_data: BillingPlanIn) -> BillingPlanOut:
        """Create a new billing plan"""
        self.logger.info("Creating new billing plan", extra={"plan_data": plan_data})

        plan = self.billing_mapper.to_model(plan_data)
        plan = await self.plan_repo.create(plan)
        if not plan:
            raise ConflictError("Plan with this ID already exists")
        return self.billing_mapper.to_out(plan)
    
    async def patch_plan(self, plan_id: str, patch_data: BillingPlanPatch) -> BillingPlanOut:
        """Partially update an existing billing plan."""

        self.logger.info(
            "Patching billing plan",
            extra={"plan_id": plan_id, "patch_data": patch_data.model_dump(exclude_unset=True)},
        )

        plan = await self.plan_repo.find_plan_by_id(plan_id)
        if not plan:
            raise BillingPlanNotFoundError(f"Billing plan {plan_id} not found")

        self.billing_mapper.patch_model(plan, patch_data)

        await self.plan_repo.save(plan)

        return self.billing_mapper.to_out(plan)


    async def create_subscription(
        self,
        merchant_id: UUID,
        shop_id: str,
        plan_id: str,
        return_url: str,
        correlation_id: str,
        test_mode: bool = False,
    ) -> SubscriptionCreateOut:
        """Create new subscription and initiate Shopify charge."""

        self.logger.set_request_context(
            merchant_id=str(merchant_id),
            correlation_id=correlation_id,
        )
        self.logger.info(
            "Creating subscription",
            extra={"plan_id": plan_id, "shop_id": shop_id},
        )

        # ----------------------------------------------------------------
        # 1. Plan & conflict checks
        # ----------------------------------------------------------------
        plan = await self.plan_repo.find_plan_by_id(plan_id)
        existing = await self.subscription_repo.find_active_by_merchant(merchant_id)
        if existing:
            raise ConflictError("Merchant already has an active subscription")

        # ----------------------------------------------------------------
        # 2. Shopify side
        # ----------------------------------------------------------------
        shopify_result = await self.shopify_client.create_subscription(
            shop_id=shop_id,
            plan_name=plan.name,
            amount=plan.price_amount,
            credits=plan.credits_included,
            billing_interval=plan.billing_interval,
            return_url=return_url,
            test_mode=test_mode,
        )

        # ----------------------------------------------------------------
        # 3. Local DB record
        # ----------------------------------------------------------------
        subscription = Subscription(
            merchant_id=merchant_id,
            shopify_subscription_id=shopify_result["appSubscription"]["id"],
            plan_id=plan_id,
            plan_name=plan.name,
            plan_description=plan.description,
            credits_included=plan.credits_included,
            price_amount=plan.price_amount,
            billing_interval=plan.billing_interval,
            status=SubscriptionStatus.PENDING,
        )
        await self.subscription_repo.save(subscription)

        # ----------------------------------------------------------------
        # 4. Publish domain event
        # ----------------------------------------------------------------
        await self.event_publisher.publish_event(
            "evt.billing.subscription.created",
            payload={
                "subscription_id": str(subscription.id),
                "merchant_id": str(merchant_id),
                "shop_id": shop_id,
                "plan_id": plan_id,
                "shopify_subscription_id": shopify_result["appSubscription"]["id"],
                "confirmation_url": shopify_result["confirmationUrl"],
                "status": SubscriptionStatus.PENDING,
                "created_at": subscription.created_at.isoformat(),
            },
            correlation_id=correlation_id,
        )

        self.logger.info(
            "Subscription created successfully",
            extra={"subscription_id": str(subscription.id)},
        )

        return SubscriptionCreateOut(
            subscription_id=subscription.id,
            confirmation_url=shopify_result["confirmationUrl"],
            status=subscription.status,
            plan_details=self.billing_mapper.to_out(plan),
        )

    async def activate_subscription_after_payment(
        self,
        shopify_subscription_id: str,
        payment_data: dict,
        correlation_id: str,
    ) -> None:
        """Mark subscription ACTIVE after successful Shopify payment."""

        subscription = await self.subscription_repo.find_by_shopify_id(
            shopify_subscription_id
        )
        if not subscription:
            raise SubscriptionNotFoundError(
                f"Subscription {shopify_subscription_id} not found"
            )

        subscription.status = SubscriptionStatus.ACTIVE
        subscription.activated_at = datetime.now(timezone.utc)
        subscription.next_billing_date = self._calculate_next_billing_date(subscription)
        await self.subscription_repo.save(subscription)

        # Credits added event
        await self.event_publisher.publish_event(
            "evt.billing.subscription.activated",
            payload={
                "subscription_id": str(subscription.id),
                "merchant_id": str(subscription.merchant_id),
                "credits_to_add": subscription.credits_included,
                "transaction_type": "SUBSCRIPTION",
                "reference_id": shopify_subscription_id,
                "activated_at": subscription.activated_at,
            },
            correlation_id=correlation_id,
        )

        # Notification event
        await self.event_publisher.publish_event(
            "evt.billing.notification.subscription_activated",
            payload={
                "merchant_id": str(subscription.merchant_id),
                "subscription_id": str(subscription.id),
                "plan_name": subscription.plan_name,
                "credits_added": subscription.credits_included,
                "next_billing_date": subscription.next_billing_date,
            },
            correlation_id=correlation_id,
        )

    # ------------------------------------------------------------------ #
    # Queries
    # ------------------------------------------------------------------ #
    async def get_all_plans(self) -> List[BillingPlanOut]:
        plans = await self.plan_repo.find_active_plans()
        return self.billing_mapper.list_to_out(plans)

    async def get_plan_by_id(self, plan_id: str) -> BillingPlanOut:
        plan = await self.plan_repo.find_plan_by_id(plan_id)
        if not plan:
            raise BillingPlanNotFoundError(f"Billing plan {plan_id} not found")
        return self.billing_mapper.to_out(plan)

    async def get_subscription(self, subscription_id: UUID) -> SubscriptionOut:
        sub = await self.subscription_repo.find_by_id(subscription_id)
        if not sub:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        return self.subscription_mapper.to_out(sub)

    async def list_merchant_subscriptions(self, merchant_id: UUID) -> List[SubscriptionOut]:
        subs = await self.subscription_repo.find_by_merchant(merchant_id)
        return self.subscription_mapper.list_to_out(subs)

    # ------------------------------------------------------------------ #
    # Commands
    # ------------------------------------------------------------------ #
    async def cancel_subscription(self, subscription_id: UUID) -> None:
        sub = await self.subscription_repo.find_by_id(subscription_id)
        if not sub:
            raise SubscriptionNotFoundError(f"Subscription {subscription_id} not found")
        await self.subscription_repo.delete(sub)

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _calculate_next_billing_date(self, subscription: Subscription) -> datetime:
        now = datetime.now(timezone.utc)
        if subscription.billing_interval == BillingInterval.MONTHLY:
            return now + timedelta(days=30)
        if subscription.billing_interval == BillingInterval.ANNUAL:
            return now + timedelta(days=365)
        return now + timedelta(days=30)
