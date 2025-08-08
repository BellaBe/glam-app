from datetime import datetime
from uuid import UUID, uuid4
import uuid7
from shared.utils.logger import ServiceLogger
from shared.api.correlation import set_correlation_context
from ..config import ServiceConfig
from ..repositories.webhook_repository import WebhookRepository
from ..events.publishers import WebhookEventPublisher
from ..models.enums import WebhookStatus, ShopifyWebhookTopic
from ..schemas.webhook import WebhookEntryOut


class WebhookProcessor:
    """Service for processing webhooks asynchronously"""
    
    def __init__(
        self,
        config: ServiceConfig,
        repository: WebhookRepository,
        publisher: WebhookEventPublisher,
        logger: ServiceLogger
    ):
        self.config = config
        self.repository = repository
        self.publisher = publisher
        self.logger = logger
    
    async def process_webhook(self, webhook_id: str, correlation_id: str) -> None:
        """Process a webhook and publish domain events"""
        set_correlation_context(correlation_id)
        
        self.logger.info(
            f"Processing webhook: {webhook_id}",
            extra={
                "webhook_id": webhook_id,
                "correlation_id": correlation_id
            }
        )
        
        try:
            # Get webhook from database
            webhook = await self.repository.find_by_id(UUID(webhook_id))
            if not webhook:
                self.logger.error(f"Webhook not found: {webhook_id}")
                return
            
            # Update status to processing
            await self.repository.update_status(
                UUID(webhook_id),
                WebhookStatus.PROCESSING
            )
            
            # Transform and publish domain event
            await self._transform_and_publish(webhook, correlation_id)
            
            # Mark as processed
            await self.repository.update_status(
                UUID(webhook_id),
                WebhookStatus.PROCESSED,
                processed_at=datetime.utcnow()
            )
            
            self.logger.info(
                f"Webhook processed successfully: {webhook_id}",
                extra={
                    "webhook_id": webhook_id,
                    "topic": webhook.topic_enum,
                    "correlation_id": correlation_id
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Error processing webhook: {webhook_id}",
                extra={
                    "webhook_id": webhook_id,
                    "error": str(e),
                    "correlation_id": correlation_id
                },
                exc_info=True
            )
            
            # Increment attempts
            webhook = await self.repository.increment_attempts(UUID(webhook_id))
            
            # Check if should retry or fail
            if webhook.processing_attempts >= self.config.webhook_max_retries:
                await self.repository.update_status(
                    UUID(webhook_id),
                    WebhookStatus.FAILED,
                    error_message=str(e)
                )
                # Could publish to DLQ here
            
            raise
    
    async def _transform_and_publish(self, webhook: WebhookEntryOut, correlation_id: str) -> None:
        """Transform webhook to domain event and publish"""
        # Map topic to handler
        topic = webhook.topic_enum
        payload = webhook.payload
        
        # Route to appropriate publisher method based on topic
        if topic == ShopifyWebhookTopic.APP_UNINSTALLED.value:
            await self.publisher.app_uninstalled(
                shop_domain=webhook.shop_domain,
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        elif topic == ShopifyWebhookTopic.APP_SUBSCRIPTIONS_UPDATE.value:
            await self.publisher.app_subscription_updated(
                shop_domain=webhook.shop_domain,
                subscription_id=payload.get('app_subscription', {}).get('admin_graphql_api_id', ''),
                status=payload.get('app_subscription', {}).get('status', ''),
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        elif topic == ShopifyWebhookTopic.APP_PURCHASES_ONE_TIME_UPDATE.value:
            await self.publisher.app_purchase_updated(
                shop_domain=webhook.shop_domain,
                charge_id=str(payload.get('app_purchase_one_time', {}).get('id', '')),
                status=payload.get('app_purchase_one_time', {}).get('status', ''),
                test=payload.get('app_purchase_one_time', {}).get('test', False),
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        elif topic == ShopifyWebhookTopic.ORDERS_CREATE.value:
            await self.publisher.order_created(
                shop_domain=webhook.shop_domain,
                order_id=str(payload.get('id', '')),
                total_price=payload.get('total_price', '0'),
                currency=payload.get('currency', 'USD'),
                created_at=payload.get('created_at', ''),
                line_items_count=len(payload.get('line_items', [])),
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        elif topic in [
            ShopifyWebhookTopic.PRODUCTS_CREATE.value,
            ShopifyWebhookTopic.PRODUCTS_UPDATE.value,
            ShopifyWebhookTopic.PRODUCTS_DELETE.value
        ]:
            event_type = topic.split('_')[-1].lower()  # create, update, delete
            await self.publisher.catalog_product_event(
                event_type=event_type,
                shop_domain=webhook.shop_domain,
                product_id=str(payload.get('id', '')),
                updated_at=payload.get('updated_at'),
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        elif topic in [
            ShopifyWebhookTopic.COLLECTIONS_CREATE.value,
            ShopifyWebhookTopic.COLLECTIONS_UPDATE.value,
            ShopifyWebhookTopic.COLLECTIONS_DELETE.value
        ]:
            event_type = topic.split('_')[-1].lower()  # create, update, delete
            await self.publisher.catalog_collection_event(
                event_type=event_type,
                shop_domain=webhook.shop_domain,
                collection_id=str(payload.get('id', '')),
                updated_at=payload.get('updated_at'),
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        elif topic == ShopifyWebhookTopic.INVENTORY_LEVELS_UPDATE.value:
            await self.publisher.inventory_updated(
                shop_domain=webhook.shop_domain,
                inventory_item_id=str(payload.get('inventory_item_id', '')),
                location_id=str(payload.get('location_id', '')),
                available=payload.get('available', 0),
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        elif topic == ShopifyWebhookTopic.CUSTOMERS_DATA_REQUEST.value:
            await self.publisher.gdpr_data_request(
                shop_domain=webhook.shop_domain,
                customer_id=payload.get('customer', {}).get('id', ''),
                orders_requested=payload.get('orders_requested', []),
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        elif topic == ShopifyWebhookTopic.CUSTOMERS_REDACT.value:
            await self.publisher.gdpr_customer_redact(
                shop_domain=webhook.shop_domain,
                customer_id=payload.get('customer', {}).get('id', ''),
                orders_to_redact=payload.get('orders_to_redact', []),
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        elif topic == ShopifyWebhookTopic.SHOP_REDACT.value:
            await self.publisher.gdpr_shop_redact(
                shop_domain=webhook.shop_domain,
                webhook_id=webhook.webhook_id,
                correlation_id=correlation_id
            )
        
        else:
            # Unknown topic - log but don't fail
            self.logger.warning(
                f"Unknown webhook topic: {topic}",
                extra={
                    "topic": topic,
                    "webhook_id": webhook.webhook_id,
                    "shop_domain": webhook.shop_domain
                }
            )


