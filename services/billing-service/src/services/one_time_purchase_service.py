# services/billing-service/src/services/one_time_purchase_service.py
class OneTimePurchaseService:
    """Service for one-time credit purchases"""
    
    def __init__(
        self,
        purchase_repo: OneTimePurchaseRepository,
        shopify_client: ShopifyBillingClient,
        event_publisher: 'BillingEventPublisher',
        logger: ServiceLogger,
        config: BillingServiceConfig
    ):
        self.purchase_repo = purchase_repo
        self.shopify_client = shopify_client
        self.event_publisher = event_publisher
        self.logger = logger
        self.config = config
    
    async def create_purchase(
        self,
        merchant_id: UUID,
        shop_id: str,
        credits: int,
        return_url: str,
        description: str = None,
        correlation_id: str = None
    ) -> dict:
        """Create one-time credit purchase"""
        
        if not description:
            description = f"{credits} Additional Credits"
        
        # Calculate price (simplified pricing)
        price_amount = Decimal(str(credits * 0.01))  # $0.01 per credit
        
        # Create Shopify charge
        shopify_result = await self.shopify_client.create_one_time_charge(
            shop_id=shop_id,
            amount=price_amount,
            description=description,
            return_url=return_url,
            test_mode=self.config.shopify_test_mode
        )
        
        # Create local purchase record
        purchase = OneTimePurchase(
            merchant_id=merchant_id,
            shopify_charge_id=shopify_result["appPurchaseOneTime"]["id"],
            credits_purchased=credits,
            price_amount=price_amount,
            description=description,
            status=PurchaseStatus.PENDING
        )
        
        await self.purchase_repo.save(purchase)
        
        # Publish purchase created event
        await self.event_publisher.publish_event(
            "evt.billing.purchase.created",
            payload={
                "purchase_id": str(purchase.id),
                "merchant_id": str(merchant_id),
                "credits_purchased": credits,
                "price_amount": str(price_amount),
                "confirmation_url": shopify_result["confirmationUrl"],
                "status": PurchaseStatus.PENDING
            },
            correlation_id=correlation_id
        )
        
        return {
            "purchase_id": purchase.id,
            "confirmation_url": shopify_result["confirmationUrl"],
            "status": purchase.status
        }
    
    async def complete_purchase(
        self,
        shopify_charge_id: str,
        payment_data: dict,
        correlation_id: str = None
    ) -> None:
        """Complete purchase after successful payment"""
        
        purchase = await self.purchase_repo.find_by_shopify_id(shopify_charge_id)
        if not purchase:
            raise BillingError("Purchase not found")
        
        # Update purchase status
        purchase.status = PurchaseStatus.COMPLETED
        purchase.completed_at = datetime.utcnow()
        
        await self.purchase_repo.save(purchase)
        
        # Publish completion event (Credit Service will add credits)
        await self.event_publisher.publish_event(
            "evt.billing.purchase.completed",
            payload={
                "purchase_id": str(purchase.id),
                "merchant_id": str(purchase.merchant_id),
                "credits_purchased": purchase.credits_purchased,
                "amount_paid": str(purchase.price_amount),
                "completed_at": purchase.completed_at.isoformat()
            },
            correlation_id=correlation_id
        )

