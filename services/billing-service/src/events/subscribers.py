# services/billing-service/src/events/subscribers.py
from shared.events import DomainEventSubscriber


class WebhookEventSubscriber(DomainEventSubscriber):
    """Subscribe to webhook events from other services"""
    
    stream_name = "WEBHOOK"
    subject = "evt.webhook.app.subscription_updated"
    event_type = "evt.webhook.app.subscription_updated"
    durable_name = "billing-subscription-updated"
    
    async def on_event(self, event: dict, headers: dict):
        """Process subscription payment webhook"""
        billing_service = self.get_dependency("billing_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        
        logger.info(
            "Processing subscription payment webhook",
            extra={
                "event_type": self.event_type,
                "correlation_id": correlation_id
            }
        )
        
        # Process subscription activation
        await billing_service.activate_subscription_after_payment(
            shopify_subscription_id=payload["subscription_id"],
            payment_data=payload,
            correlation_id=correlation_id
        )


class PurchaseWebhookSubscriber(DomainEventSubscriber):
    """Subscribe to purchase webhook events"""
    
    stream_name = "WEBHOOK"
    subject = "evt.webhook.app.purchase_updated"
    event_type = "evt.webhook.app.purchase_updated"
    durable_name = "billing-purchase-updated"
    
    async def on_event(self, event: dict, headers: dict):
        """Process purchase payment webhook"""
        purchase_service = self.get_dependency("purchase_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        
        logger.info(
            "Processing purchase payment webhook",
            extra={
                "event_type": self.event_type,
                "correlation_id": correlation_id
            }
        )
        
        # Process purchase completion
        await purchase_service.complete_purchase(
            shopify_charge_id=payload["charge_id"],
            payment_data=payload,
            correlation_id=correlation_id
        )


class AppUninstalledSubscriber(DomainEventSubscriber):
    """Subscribe to app uninstallation events"""
    
    stream_name = "WEBHOOK"
    subject = "evt.webhook.app.uninstalled"
    event_type = "evt.webhook.app.uninstalled"
    durable_name = "billing-app-uninstalled"
    
    async def on_event(self, event: dict, headers: dict):
        """Cancel all subscriptions on app uninstall"""
        billing_service = self.get_dependency("billing_service")
        logger = self.get_dependency("logger")
        
        payload = event["payload"]
        correlation_id = event.get("correlation_id")
        
        logger.info(
            "Processing app uninstall",
            extra={
                "shop_id": payload.get("shop_id"),
                "correlation_id": correlation_id
            }
        )
        
        # Cancel all active subscriptions for the shop
        # Implementation would find and cancel subscriptions