# services/catalog-service/src/events/inbound.py

"""
Events that the CATALOG SERVICE listens for (from other services)
"""

from shared.events.payloads.common import MerchantCreatedPayload, WebhookReceivedPayload


class CatalogInboundEvents:
    """Events the catalog service subscribes to"""
    
    # System events
    MERCHANT_CREATED = "merchant.created.v1"  # Initialize catalog
    
    # Webhook events (product updates from platforms)
    WEBHOOK_RECEIVED = "webhook.received.v1"  # Filter for product webhooks
    
    # Manual sync requests
    SYNC_REQUESTED = "catalog.sync_requested.v1"  # From API or admin
    
    PAYLOAD_SCHEMAS: Dict[str, Type[BaseModel]] = {
        MERCHANT_CREATED: MerchantCreatedPayload,
        WEBHOOK_RECEIVED: WebhookReceivedPayload,
    }
    
    @classmethod
    def handles_webhook_type(cls, webhook_type: str) -> bool:
        """Check if we handle this webhook type"""
        product_webhooks = [
            "products/create",
            "products/update", 
            "products/delete",
            "inventory_levels/update"
        ]
        return webhook_type in product_webhooks