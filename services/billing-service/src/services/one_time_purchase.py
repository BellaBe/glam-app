# services/billing-service/src/services/one_time_purchase_service.py
"""Service for one-time credit purchases."""

from datetime import datetime, timezone
from typing import Optional

from shared.api.dependencies import RequestContextDep
from shared.utils.logger import ServiceLogger
from ..events import BillingEventPublisher
from ..external import ShopifyBillingClient
from ..models import OneTimePurchase, PurchaseStatus
from ..repositories import OneTimePurchaseRepository
from ..config import BillingServiceConfig
from ..exceptions import ConflictError
from ..mappers import OneTimePurchaseMapper
from ..schemas import OneTimePurchaseIn, OneTimePurchaseOut

class OneTimePurchaseService:
    """Service for one-time credit purchases"""
    
    def __init__(
        self,
        purchase_repo: OneTimePurchaseRepository,
        shopify_client: ShopifyBillingClient,
        event_publisher: BillingEventPublisher,
        logger: ServiceLogger,
        config: BillingServiceConfig
    ):
        self.purchase_repo = purchase_repo
        self.shopify_client = shopify_client
        self.event_publisher = event_publisher
        self.logger = logger
        self.config = config
        self.mapper = OneTimePurchaseMapper()
    
    async def create_purchase(
        self,
        data: OneTimePurchaseIn,
        ctx: RequestContextDep
    ) -> OneTimePurchaseOut:
        """Create one-time credit purchase"""
        
        self.logger.set_request_context(
            merchant_id=str(data.merchant_id),
            correlation_id=ctx.correlation_id
        )
        self.logger.info("Creating one-time purchase", extra={
            "merchant_id": str(data.merchant_id),
            "credits_purchased": data.credits_purchased,
            "description": data.description
        })
        
        # Generate return URL for Shopify
        return_url = f"{self.config.frontend_url}/billing/purchase/confirmation?merchant_id={data.merchant_id}&correlation_id={ctx.correlation_id}"
        
        
        # Create Shopify charge
        shopify_result = await self.shopify_client.create_one_time_charge(
            shop_id=str(data.merchant_id),
            amount=data.price_amount,
            description=data.description,
            return_url=return_url,
            test_mode=self.config.shopify_test_mode
        )
        
        # Create local purchase record
        purchase = OneTimePurchase(
            merchant_id=data.merchant_id,
            shopify_charge_id=shopify_result["appPurchaseOneTime"]["id"],
            credits_purchased=credits,
            price_amount=data.price_amount,
            description=data.description,
            status=PurchaseStatus.PENDING
        )
        
        await self.purchase_repo.save(purchase)
        
        # Publish purchase created event
        await self.event_publisher.publish_event(
            "evt.billing.purchase.created",
            payload={
                "purchase_id": str(purchase.id),
                "merchant_id": str(data.merchant_id),
                "credits_purchased": data.credits_purchased,
                "price_amount": str(data.price_amount),
                "confirmation_url": shopify_result["confirmationUrl"],
                "status": PurchaseStatus.PENDING
            },
            correlation_id=ctx.correlation_id
        )
        
        return self.mapper.to_out(purchase)
    
    async def complete_purchase(
        self,
        shopify_charge_id: str,
        payment_data: dict,
        correlation_id: Optional[str] = None
    ) -> None:
        """Complete purchase after successful payment"""
        
        purchase = await self.purchase_repo.find_by_shopify_id(shopify_charge_id)
        if not purchase:
            raise ConflictError(f"Purchase not found for charge ID {shopify_charge_id}")

        # Update purchase status
        purchase.status = PurchaseStatus.COMPLETED
        purchase.completed_at = datetime.now(timezone.utc)
        
        await self.purchase_repo.save(purchase)
        
        # Publish completion event (Credit Service will add credits)
        await self.event_publisher.publish_event(
            "evt.billing.purchase.completed",
            payload={
                "purchase_id": str(purchase.id),
                "merchant_id": str(purchase.merchant_id),
                "credits_purchased": purchase.credits_purchased,
                "amount_paid": str(purchase.price_amount),
                "completed_at": purchase.completed_at
            },
            correlation_id=correlation_id
        )

