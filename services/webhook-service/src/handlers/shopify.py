# services/webhook-service/src/handlers/shopify.py
"""Shopify webhook handler."""

import hashlib
from typing import Dict, Any, Optional
from datetime import datetime

from .base import WebhookHandler, WebhookData, DomainEvent


class ShopifyWebhookHandler(WebhookHandler):
    """Handler for Shopify webhooks"""
    
    # Topic to domain event mapping
    TOPIC_EVENT_MAP = {
        # App lifecycle
        "app/uninstalled": "evt.webhook.app.uninstalled",
        "app_subscriptions/update": "evt.webhook.app.subscription_updated",
        "app_purchases_one_time/update": "evt.webhook.app.purchase_updated",
        
        # Catalog
        "products/create": "evt.webhook.catalog.item_created",
        "products/update": "evt.webhook.catalog.item_updated",
        "products/delete": "evt.webhook.catalog.item_deleted",
        
        # Orders
        "orders/create": "evt.webhook.order.created",
        "orders/updated": "evt.webhook.order.updated",
        "orders/fulfilled": "evt.webhook.order.fulfilled",
        "orders/cancelled": "evt.webhook.order.cancelled",
        
        # Inventory
        "inventory_levels/update": "evt.webhook.inventory.updated",
        "inventory_items/update": "evt.webhook.inventory.item_updated",
        
        # Compliance (no domain events)
        "customers/data_request": None,
        "customers/redact": None,
        "shop/redact": None,
    }
    
    def parse_webhook(
        self, 
        body: Dict[str, Any], 
        topic: Optional[str],
        headers: Dict[str, str]
    ) -> WebhookData:
        """Parse Shopify webhook"""
        
        # Get topic from header if not in path
        if not topic:
            topic = headers.get('x-shopify-topic', 'unknown')
        
        # Extract shop info
        shop_domain = headers.get('x-shopify-shop-domain', '')
        shop_id = shop_domain.split('.')[0] if shop_domain else None
        
        # Generate idempotency key
        idempotency_key = self.get_idempotency_key(body, topic, headers)
        
        # Build metadata
        metadata = {
            'webhook_id': headers.get('x-shopify-webhook-id'),
            'api_version': headers.get('x-shopify-api-version'),
            'triggered_at': headers.get('x-shopify-triggered-at'),
        }
        
        return WebhookData(
            topic=topic,
            shop_id=shop_id,
            shop_domain=shop_domain,
            idempotency_key=idempotency_key,
            payload=body,
            metadata={k: v for k, v in metadata.items() if v}
        )
    
    def get_idempotency_key(
        self, 
        body: Dict[str, Any], 
        topic: str,
        headers: Dict[str, str]
    ) -> str:
        """Generate idempotency key for Shopify webhook"""
        
        # Use webhook ID if available
        webhook_id = headers.get('x-shopify-webhook-id')
        if webhook_id:
            return f"shopify:{webhook_id}"
        
        # Fallback to hash of key components
        shop_domain = headers.get('x-shopify-shop-domain', '')
        
        # For orders/products, use their ID
        if 'id' in body:
            key_parts = f"shopify:{topic}:{shop_domain}:{body['id']}"
        else:
            # Hash the entire payload as last resort
            payload_hash = hashlib.sha256(
                str(body).encode()
            ).hexdigest()[:16]
            key_parts = f"shopify:{topic}:{shop_domain}:{payload_hash}"
        
        return hashlib.sha256(key_parts.encode()).hexdigest()
    
    def map_to_domain_event(
        self, 
        webhook_data: WebhookData
    ) -> Optional[DomainEvent]:
        """Map Shopify webhook to domain event"""
        
        event_type = self.TOPIC_EVENT_MAP.get(webhook_data.topic)
        if not event_type:
            self.logger.debug(
                f"No domain event mapping for topic: {webhook_data.topic}"
            )
            return None
        
        # Build event payload based on topic
        payload = self._build_event_payload(
            webhook_data.topic,
            webhook_data.payload,
            webhook_data.shop_id,
            webhook_data.shop_domain
        )
        
        return DomainEvent(
            event_type=event_type,
            payload=payload
        )
    
    def _build_event_payload(
        self,
        topic: str,
        webhook_payload: Dict[str, Any],
        shop_id: Optional[str],
        shop_domain: Optional[str]
    ) -> Dict[str, Any]:
        """Build domain event payload based on topic"""
        
        base_payload = {
            "shop_id": shop_id,
            "shop_domain": shop_domain,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # App lifecycle events
        if topic == "app/uninstalled":
            return {**base_payload}
        
        elif topic == "app_subscriptions/update":
            subscription = webhook_payload
            return {
                **base_payload,
                "subscription_id": str(subscription.get("id")),
                "status": subscription.get("status"),
                "plan": subscription.get("name"),
                "trial_ends_at": subscription.get("trial_ends_on")
            }
        
        # Product events
        elif topic.startswith("products/"):
            product = webhook_payload
            payload = {
                **base_payload,
                "item_id": str(product.get("id")),
                "external_id": str(product.get("id")),
                "title": product.get("title"),
                "vendor": product.get("vendor"),
                "product_type": product.get("product_type"),
                "status": product.get("status"),
            }
            
            if topic == "products/update":
                # Add change detection (simplified)
                payload["changes"] = ["data"]  # Would need previous state
            
            return payload
        
        # Order events
        elif topic.startswith("orders/"):
            order = webhook_payload
            return {
                **base_payload,
                "order_id": str(order.get("id")),
                "order_number": order.get("order_number"),
                "total": order.get("total_price"),
                "currency": order.get("currency"),
                "financial_status": order.get("financial_status"),
                "fulfillment_status": order.get("fulfillment_status"),
                "customer_id": str(order.get("customer", {}).get("id", "")),
                "items": [
                    {
                        "item_id": str(item.get("product_id")),
                        "variant_id": str(item.get("variant_id")),
                        "quantity": item.get("quantity"),
                        "price": item.get("price")
                    }
                    for item in order.get("line_items", [])
                ]
            }
        
        # Inventory events
        elif topic == "inventory_levels/update":
            return {
                **base_payload,
                "item_id": str(webhook_payload.get("inventory_item_id")),
                "location_id": str(webhook_payload.get("location_id")),
                "available": webhook_payload.get("available"),
                "updated_at": webhook_payload.get("updated_at")
            }
        
        elif topic == "inventory_items/update":
            item = webhook_payload
            return {
                **base_payload,
                "item_id": str(item.get("id")),
                "sku": item.get("sku"),
                "tracked": item.get("tracked"),
                "requires_shipping": item.get("requires_shipping")
            }
        
        # Default fallback
        return {
            **base_payload,
            "data": webhook_payload
        }