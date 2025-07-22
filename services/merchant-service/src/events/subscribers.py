# services/merchant-service/src/events/subscribers.py
from shared.events import DomainEventSubscriber
from ..models.enums import MerchantStatusEnum

class WebhookAppInstalledSubscriber(DomainEventSubscriber):
    """Subscribe to app installation events from webhook service"""
    stream_name = "WEBHOOK"
    subject = "evt.webhook.app.installed"
    event_type = "evt.webhook.app.installed"
    durable_name = "merchant-app-installed"
    
    async def on_event(self, event: dict, headers: dict):
        """Handle app installation from Shopify"""
        service = self.get_dependency("merchant_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        
        logger.info(
            "Processing app installation event",
            extra={
                "event_type": self.event_type,
                "correlation_id": correlation_id,
                "shop_id": payload.get("shop_id")
            }
        )
        
        # Process with service
        await service.handle_app_installed(payload, correlation_id)

class BillingSubscriptionActivatedSubscriber(DomainEventSubscriber):
    """Subscribe to subscription activation from billing service"""
    stream_name = "BILLING"
    subject = "evt.billing.subscription.activated"
    event_type = "evt.billing.subscription.activated"
    durable_name = "merchant-subscription-activated"
    
    async def on_event(self, event: dict, headers: dict):
        """Handle subscription activation"""
        service = self.get_dependency("merchant_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        merchant_id = payload["merchant_id"]
        
        logger.info(
            "Processing subscription activation",
            extra={
                "event_type": self.event_type,
                "merchant_id": merchant_id
            }
        )
        
        await service.update_merchant_status(
            merchant_id,
            MerchantStatusEnum.ACTIVE,
            "subscription_activated"
        )
