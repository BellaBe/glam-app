# services/webhook-service/src/handlers/stripe.py
"""Stripe webhook handler."""

import hashlib
from typing import Dict, Any, Optional

from .base import WebhookHandler, WebhookData, DomainEvent


class StripeWebhookHandler(WebhookHandler):
    """Handler for Stripe webhooks"""
    
    # Event type to domain event mapping
    EVENT_TYPE_MAP = {
        # Payment events
        "payment_intent.succeeded": "evt.webhook.payment.succeeded",
        "payment_intent.failed": "evt.webhook.payment.failed",
        
        # Subscription events
        "customer.subscription.created": "evt.webhook.subscription.created",
        "customer.subscription.updated": "evt.webhook.subscription.updated",
        "customer.subscription.deleted": "evt.webhook.subscription.cancelled",
        
        # Customer events
        "customer.created": "evt.webhook.customer.created",
        "customer.updated": "evt.webhook.customer.updated",
    }
    
    def parse_webhook(
        self, 
        body: Dict[str, Any], 
        topic: Optional[str],
        headers: Dict[str, str]
    ) -> WebhookData:
        """Parse Stripe webhook"""
        
        # Extract event type
        event_type = body.get("type", "unknown")
        if topic and topic != event_type:
            self.logger.warning(
                f"Topic mismatch: path={topic}, body={event_type}"
            )
        
        # Extract data
        data = body.get("data", {}).get("object", {})
        
        # Get shop info from metadata if available
        metadata = data.get("metadata", {})
        shop_id = metadata.get("shop_id")
        shop_domain = metadata.get("shop_domain")
        
        # Generate idempotency key
        idempotency_key = self.get_idempotency_key(body, event_type, headers)
        
        # Build metadata
        webhook_metadata = {
            "event_id": body.get("id"),
            "api_version": body.get("api_version"),
            "created": body.get("created"),
            "livemode": body.get("livemode"),
        }
        
        return WebhookData(
            topic=event_type,
            shop_id=shop_id,
            shop_domain=shop_domain,
            idempotency_key=idempotency_key,
            payload=data,
            metadata=webhook_metadata
        )
    
    def get_idempotency_key(
        self, 
        body: Dict[str, Any], 
        topic: str,
        headers: Dict[str, str]
    ) -> str:
        """Generate idempotency key for Stripe webhook"""
        
        # Use event ID
        event_id = body.get("id")
        if event_id:
            return f"stripe:{event_id}"
        
        # Fallback (shouldn't happen with valid Stripe events)
        payload_hash = hashlib.sha256(
            str(body).encode()
        ).hexdigest()[:16]
        
        return f"stripe:{topic}:{payload_hash}"
    
    def map_to_domain_event(
        self, 
        webhook_data: WebhookData
    ) -> Optional[DomainEvent]:
        """Map Stripe webhook to domain event"""
        
        event_type = self.EVENT_TYPE_MAP.get(webhook_data.topic)
        if not event_type:
            self.logger.debug(
                f"No domain event mapping for Stripe event: {webhook_data.topic}"
            )
            return None
        
        # Build event payload
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
        event_type: str,
        stripe_data: Dict[str, Any],
        shop_id: Optional[str],
        shop_domain: Optional[str]
    ) -> Dict[str, Any]:
        """Build domain event payload for Stripe events"""
        
        base_payload = {
            "shop_id": shop_id,
            "shop_domain": shop_domain,
            "stripe_object_id": stripe_data.get("id"),
            "created": stripe_data.get("created")
        }
        
        # Payment events
        if event_type.startswith("payment_intent."):
            return {
                **base_payload,
                "payment_intent_id": stripe_data.get("id"),
                "amount": stripe_data.get("amount"),
                "currency": stripe_data.get("currency"),
                "status": stripe_data.get("status"),
                "customer_id": stripe_data.get("customer"),
            }
        
        # Subscription events
        elif event_type.startswith("customer.subscription."):
            return {
                **base_payload,
                "subscription_id": stripe_data.get("id"),
                "customer_id": stripe_data.get("customer"),
                "status": stripe_data.get("status"),
                "plan_id": stripe_data.get("items", {}).get("data", [{}])[0].get("price", {}).get("id"),
                "current_period_end": stripe_data.get("current_period_end"),
            }
        
        # Customer events
        elif event_type.startswith("customer."):
            return {
                **base_payload,
                "customer_id": stripe_data.get("id"),
                "email": stripe_data.get("email"),
                "name": stripe_data.get("name"),
            }
        
        # Default
        return {
            **base_payload,
            "data": stripe_data
        }