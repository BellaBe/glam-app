# services/billing-service/src/events/subscribers.py
from shared.events import DomainEventSubscriber


class WebhookEventSubscriber(DomainEventSubscriber):
    """Subscribe to webhook events from other services"""

    @property
    def subject(self) -> str:
        return WebhookEvents.SUBSCRIPTION_UPDATED

    @property
    def subject(self) -> str:
        return WebhookEvents.SUBSCRIPTION_UPDATED

    @property
    def durable_name(self) -> str:
        return "billing-subscription-updated"

    async def on_event(self, event: dict, headers=None):
        """Process subscription payment webhook"""
        billing_service = self.get_dependency("billing_service")  # type: ignore
        logger = self.get_dependency("logger")

        payload = event["payload"]
        correlation_id = event.get("correlation_id")

        logger.info(
            "Processing subscription payment webhook",
            extra={"subject": self.subject, "correlation_id": correlation_id},
        )

        # Process subscription activation
        await billing_service.activate_subscription_after_payment(
            shopify_subscription_id=payload["subscription_id"],
            payment_data=payload,
            correlation_id=correlation_id,
        )


class PurchaseWebhookSubscriber(DomainEventSubscriber):
    """Subscribe to purchase webhook events"""

    @property
    def subject(self) -> str:
        """The subject pattern to subscribe to"""
        return WebhookEvents.PURCHASE_UPDATED

    @property
    def subject(self) -> str:
        """The expected subject for validation"""
        return WebhookEvents.PURCHASE_UPDATED

    @property
    def durable_name(self) -> str:
        """The durable consumer name"""
        return "billing-purchase-updated"

    async def on_event(self, event: dict, headers=None):
        """Process purchase payment webhook"""
        purchase_service = self.get_dependency("purchase_service")  # type: ignore
        logger = self.get_dependency("logger")

        payload = event["payload"]
        correlation_id = event.get("correlation_id")

        logger.info(
            "Processing purchase payment webhook",
            extra={"subject": self.subject, "correlation_id": correlation_id},
        )

        # Process purchase completion
        await purchase_service.complete_purchase(
            shopify_charge_id=payload["charge_id"],
            payment_data=payload,
            correlation_id=correlation_id,
        )


class AppUninstalledSubscriber(DomainEventSubscriber):
    """Subscribe to app uninstallation events"""

    @property
    def subject(self) -> str:
        """The expected subject for validation"""
        return WebhookEvents.APP_UNINSTALLED

    @property
    def subject(self) -> str:
        """The subject pattern to subscribe to"""
        return WebhookEvents.APP_UNINSTALLED

    @property
    def durable_name(self) -> str:
        """The durable consumer name"""
        return "billing-app-uninstalled"

    async def on_event(self, event: dict, headers=None):
        """Cancel all subscriptions on app uninstall"""
        billing_service = self.get_dependency("billing_service")  # type: ignore
        logger = self.get_dependency("logger")

        payload = event["payload"]
        correlation_id = event.get("correlation_id")

        logger.info(
            "Processing app uninstall",
            extra={"shop_id": payload.get("shop_id"), "correlation_id": correlation_id},
        )
        # Cancel all subscriptions for the shop
        await billing_service.cancel_all_subscriptions(
            shop_id=payload["shop_id"], correlation_id=correlation_id
        )
