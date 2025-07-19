# services/billing-service/src/services/billing_service.py
from shared.errors import NotFoundError, ValidationError
from shared.utils.logger import ServiceLogger
from datetime import datetime, timedelta
import redis.asyncio as redis


class BillingError(Exception):
    """Billing service error"""
    pass


class BillingService:
    """Main billing service for subscription and payment management"""
    
    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        plan_repo: BillingPlanRepository,
        shopify_client: ShopifyBillingClient,
        event_publisher: 'BillingEventPublisher',
        redis_client: redis.Redis,
        logger: ServiceLogger,
        config: BillingServiceConfig
    ):
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.shopify_client = shopify_client
        self.event_publisher = event_publisher
        self.redis_client = redis_client
        self.logger = logger
        self.config = config
    
    async def create_subscription(
        self,
        merchant_id: UUID,
        shop_id: str,
        plan_id: str,
        return_url: str,
        test_mode: bool = False,
        correlation_id: str = None
    ) -> SubscriptionCreateResponse:
        """Create new subscription and initiate Shopify charge"""
        
        self.logger.set_request_context(
            merchant_id=str(merchant_id),
            correlation_id=correlation_id
        )
        
        self.logger.info(
            "Creating subscription",
            extra={"plan_id": plan_id, "shop_id": shop_id}
        )
        
        # Get plan details
        plan = await self.plan_repo.find_by_id(plan_id)
        if not plan or not plan.is_active:
            raise BillingError("Invalid or inactive plan")
        
        # Check for existing active subscription
        existing = await self.subscription_repo.find_active_by_merchant(merchant_id)
        if existing:
            raise BillingError("Merchant already has active subscription")
        
        # Create Shopify subscription charge
        shopify_result = await self.shopify_client.create_subscription(
            shop_id=shop_id,
            plan_name=plan.name,
            amount=plan.price_amount,
            credits=plan.credits_included,
            billing_interval=plan.billing_interval,
            return_url=return_url,
            test_mode=test_mode
        )
        
        # Create local subscription record
        subscription = Subscription(
            merchant_id=merchant_id,
            shopify_subscription_id=shopify_result["appSubscription"]["id"],
            plan_id=plan_id,
            plan_name=plan.name,
            plan_description=plan.description,
            credits_included=plan.credits_included,
            price_amount=plan.price_amount,
            billing_interval=plan.billing_interval,
            status=SubscriptionStatus.PENDING
        )
        
        await self.subscription_repo.save(subscription)
        
        # Publish subscription created event
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
                "created_at": subscription.created_at.isoformat()
            },
            correlation_id=correlation_id
        )
        
        self.logger.info(
            "Subscription created successfully",
            extra={"subscription_id": str(subscription.id)}
        )
        
        return SubscriptionCreateResponse(
            subscription_id=subscription.id,
            confirmation_url=shopify_result["confirmationUrl"],
            status=subscription.status,
            plan_details=plan.__dict__
        )
    
    async def activate_subscription_after_payment(
        self,
        shopify_subscription_id: str,
        payment_data: dict,
        correlation_id: str = None
    ) -> None:
        """Activate subscription after successful Shopify payment"""
        
        subscription = await self.subscription_repo.find_by_shopify_id(shopify_subscription_id)
        if not subscription:
            raise BillingError("Subscription not found")
        
        # Update subscription status
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.activated_at = datetime.utcnow()
        subscription.next_billing_date = self._calculate_next_billing_date(subscription)
        
        await self.subscription_repo.save(subscription)
        
        # Publish activation event (Credit Service will add credits)
        await self.event_publisher.publish_event(
            "evt.billing.subscription.activated",
            payload={
                "subscription_id": str(subscription.id),
                "merchant_id": str(subscription.merchant_id),
                "credits_to_add": subscription.credits_included,
                "transaction_type": "SUBSCRIPTION",
                "reference_id": shopify_subscription_id,
                "activated_at": subscription.activated_at.isoformat()
            },
            correlation_id=correlation_id
        )
        
        # Trigger welcome email
        await self.event_publisher.publish_event(
            "evt.billing.notification.subscription_activated",
            payload={
                "merchant_id": str(subscription.merchant_id),
                "subscription_id": str(subscription.id),
                "plan_name": subscription.plan_name,
                "credits_added": subscription.credits_included,
                "next_billing_date": subscription.next_billing_date.isoformat() if subscription.next_billing_date else None
            },
            correlation_id=correlation_id
        )
    
    def _calculate_next_billing_date(self, subscription: Subscription) -> datetime:
        """Calculate next billing date based on interval"""
        now = datetime.utcnow()
        if subscription.billing_interval == BillingInterval.MONTHLY:
            return now + timedelta(days=30)
        elif subscription.billing_interval == BillingInterval.ANNUAL:
            return now + timedelta(days=365)
        return now + timedelta(days=30)
    
    async def get_subscription(self, subscription_id: UUID) -> Optional[Subscription]:
        """Get subscription by ID"""
        return await self.subscription_repo.find_by_id(subscription_id)
    
    async def list_merchant_subscriptions(self, merchant_id: UUID) -> List[Subscription]:
        """List all subscriptions for merchant"""
        return await self.subscription_repo.find_by_merchant(merchant_id)
