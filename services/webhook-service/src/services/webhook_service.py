# services/webhook-service/src/services/webhook_service.py
from typing import Any

from shared.utils.logger import ServiceLogger

from ..config import ServiceConfig
from ..events.publishers import WebhookEventPublisher
from ..models import ShopifyWebhookTopic, WebhookPlatform
from ..repositories.webhook_repository import WebhookRepository


class WebhookService:
    def __init__(
        self,
        config: ServiceConfig,
        repository: WebhookRepository,
        publisher: WebhookEventPublisher,
        logger: ServiceLogger,
    ):
        self.config = config
        self.repository = repository
        self.publisher = publisher
        self.logger = logger

    async def receive_webhook(
        self,
        *,
        platform: WebhookPlatform,
        topic: ShopifyWebhookTopic,
        domain: str,
        webhook_id: str,
        payload: dict,
        correlation_id: str,
    ) -> str:
        """
        Store webhook and publish domain events if new.
        Returns the webhook entry ID.
        """

        if topic is ShopifyWebhookTopic.UNKNOWN:
            self.logger.warning(
                "Received webhook with unknown topic",
                extra={
                    "topic_enum": topic.name,
                    "topic": topic.value,
                    "domain": domain,
                    "webhook_id": webhook_id,
                    "correlation_id": correlation_id,
                },
            )

        # Store the webhook
        entry, is_new = await self.repository.create_or_get_existing(
            platform=platform.value,
            webhook_id=webhook_id,
            topic=topic.value,
            domain=domain,
            payload=payload,
        )

        if not is_new:
            # Duplicate webhook - already processed
            self.logger.info(
                "Duplicate webhook received",
                extra={
                    "topic_enum": topic.name,
                    "topic": topic.value,
                    "domain": domain,
                    "webhook_id": webhook_id,
                    "correlation_id": correlation_id,
                    "entry_id": entry.id,
                },
            )
            return entry.id

        await self._publish_domain_event(
            topic=topic,
            domain=domain,
            webhook_id=webhook_id,
            payload=payload,
            correlation_id=correlation_id,
        )

        self.logger.info(
            "New webhook stored & events published",
            extra={
                "topic": topic,
                "topic_enum": topic.value,
                "domain": domain,
                "webhook_id": webhook_id,
                "correlation_id": correlation_id,
                "entry_id": entry.id,
            },
        )

        return entry.id

    async def _publish_domain_event(
        self,
        topic: ShopifyWebhookTopic,
        domain: str,
        webhook_id: str,
        payload: dict[Any, Any],
        correlation_id: str,
    ) -> None:
        """Publish appropriate domain event based on webhook topic"""

        # Map webhook topics to domain events
        if topic is ShopifyWebhookTopic.APP_UNINSTALLED:
            await self.publisher.app_uninstalled(
                domain=domain,
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        elif topic is ShopifyWebhookTopic.ORDERS_CREATE:
            await self.publisher.order_created(
                domain=domain,
                order_id=str(payload.get("id", "")),
                total_price=payload.get("total_price", "0.00"),
                currency=payload.get("currency", "USD"),
                created_at=payload.get("created_at", ""),
                line_items_count=len(payload.get("line_items", [])),
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        elif topic is ShopifyWebhookTopic.APP_SUBSCRIPTIONS_UPDATE:
            subscription = payload.get("app_subscription", {})
            await self.publisher.app_subscription_updated(
                domain=domain,
                subscription_id=str(subscription.get("id", "")),
                status=subscription.get("status", ""),
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        elif topic is ShopifyWebhookTopic.APP_PURCHASES_ONE_TIME_UPDATE:
            purchase = payload.get("app_purchase_one_time", {})
            await self.publisher.app_purchase_updated(
                domain=domain,
                charge_id=str(purchase.get("id", "")),
                status=purchase.get("status", ""),
                test=purchase.get("test", False),
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        elif topic in (
            ShopifyWebhookTopic.PRODUCTS_CREATE,
            ShopifyWebhookTopic.PRODUCTS_UPDATE,
            ShopifyWebhookTopic.PRODUCTS_DELETE,
        ):
            action_map = {
                ShopifyWebhookTopic.PRODUCTS_CREATE: "created",
                ShopifyWebhookTopic.PRODUCTS_UPDATE: "updated",
                ShopifyWebhookTopic.PRODUCTS_DELETE: "deleted",
            }
            event_type = action_map[topic]
            await self.publisher.catalog_product_event(
                event_type=event_type,
                domain=domain,
                product_id=str(payload.get("id", "")),
                updated_at=payload.get("updated_at") if event_type == "updated" else None,
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        elif topic in (
            ShopifyWebhookTopic.COLLECTIONS_CREATE,
            ShopifyWebhookTopic.COLLECTIONS_UPDATE,
            ShopifyWebhookTopic.COLLECTIONS_DELETE,
        ):
            action_map = {
                ShopifyWebhookTopic.COLLECTIONS_CREATE: "created",
                ShopifyWebhookTopic.COLLECTIONS_UPDATE: "updated",
                ShopifyWebhookTopic.COLLECTIONS_DELETE: "deleted",
            }
            event_type = action_map[topic]
            await self.publisher.catalog_collection_event(
                event_type=event_type,
                domain=domain,
                collection_id=str(payload.get("id", "")),
                updated_at=payload.get("updated_at") if event_type == "updated" else None,
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        elif topic is ShopifyWebhookTopic.INVENTORY_LEVELS_UPDATE:
            await self.publisher.inventory_updated(
                domain=domain,
                inventory_item_id=str(payload.get("inventory_item_id", "")),
                location_id=str(payload.get("location_id", "")),
                available=payload.get("available", 0),
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        elif topic is ShopifyWebhookTopic.CUSTOMERS_DATA_REQUEST:
            customer = payload.get("customer", {})
            await self.publisher.gdpr_data_request(
                domain=domain,
                customer_id=str(customer.get("id", "")),
                orders_requested=payload.get("orders_requested", []),
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        elif topic is ShopifyWebhookTopic.CUSTOMERS_REDACT:
            customer = payload.get("customer", {})
            await self.publisher.gdpr_customer_redact(
                domain=domain,
                customer_id=str(customer.get("id", "")),
                orders_to_redact=payload.get("orders_to_redact", []),
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        elif topic is ShopifyWebhookTopic.SHOP_REDACT:
            await self.publisher.gdpr_shop_redact(
                domain=domain,
                webhook_id=webhook_id,
                correlation_id=correlation_id,
            )

        else:
            self.logger.warning(
                f"No domain event mapping for topic: {topic}",
                extra={
                    "topic": topic.value,
                    "domain": domain,
                    "correlation_id": correlation_id,
                },
            )
