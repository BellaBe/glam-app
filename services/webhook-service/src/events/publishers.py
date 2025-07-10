# services/webhook-service/src/events/publishers.py
"""Event publishers for webhook service."""

from shared.events import (
    Streams,
    DomainEventPublisher,
    EventContextManager,
    EventContext,
)
from shared.events.webhook.types import (
    WebhookEvents,
    WebhookReceivedPayload,
    WebhookProcessedPayload,
    WebhookFailedPayload,
    ValidationFailedPayload,
)
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone


class WebhookEventPublisher(DomainEventPublisher):
    """Publisher for webhook service events"""

    domain_stream = Streams.WEBHOOK
    service_name_override = "webhook-service"

    def __init__(self, client, js, logger=None):
        super().__init__(client, js, logger)
        self.context_manager = EventContextManager(logger or self.logger)

    async def publish_webhook_received(
        self,
        source: str,
        topic: str,
        merchant_id: Optional[str] = None,
        shop_domain: Optional[str] = None,
        webhook_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Publish webhook received event"""
        context = EventContext(
            event_id=str(UUID()),
            event_type=WebhookEvents.WEBHOOK_RECEIVED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override,
            metadata={
                **(metadata or {}),
                "source": source,
                "topic": topic,
                "webhook_id": webhook_id,
            },
        )

        payload = WebhookReceivedPayload(
            source=source,
            topic=topic,
            merchant_id=merchant_id,
            shop_domain=shop_domain,
            webhook_id=webhook_id,
            received_at=context.timestamp,
        )

        return await self.publish_with_context(context, payload)

    async def publish_validation_failed(
        self,
        source: str,
        reason: str,
        topic: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Publish validation failed event"""
        context = EventContext(
            event_id=str(UUID()),
            event_type=WebhookEvents.VALIDATION_FAILED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override,
            metadata={**(metadata or {}), "source": source, "reason": reason},
        )

        payload = ValidationFailedPayload(
            source=source, reason=reason, topic=topic, failed_at=context.timestamp
        )

        return await self.publish_with_context(context, payload)

    async def publish_webhook_processed(
        self,
        entry_id: str,
        source: str,
        topic: str,
        event_type: str,
        merchant_id: Optional[str] = None,
        shop_domain: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Publish webhook processed event"""
        context = EventContext(
            event_id=str(UUID()),
            event_type=WebhookEvents.WEBHOOK_PROCESSED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override,
            metadata={
                **(metadata or {}),
                "entry_id": entry_id,
                "mapped_event": event_type,
            },
        )

        payload = WebhookProcessedPayload(
            entry_id=entry_id,
            source=source,
            topic=topic,
            event_type=event_type,
            merchant_id=merchant_id,
            shop_domain=shop_domain,
            processed_at=context.timestamp,
        )

        return await self.publish_with_context(context, payload)

    async def publish_webhook_failed(
        self,
        entry_id: str,
        source: str,
        topic: str,
        error: str,
        attempts: int,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Publish webhook failed event"""
        context = EventContext(
            event_id=str(UUID()),
            event_type=WebhookEvents.WEBHOOK_FAILED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override,
            metadata={**(metadata or {}), "entry_id": entry_id, "attempts": attempts},
        )

        payload = WebhookFailedPayload(
            entry_id=entry_id,
            source=source,
            topic=topic,
            error=error,
            attempts=attempts,
            failed_at=context.timestamp,
        )

        return await self.publish_with_context(context, payload)

    async def publish_domain_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Publish mapped domain event (e.g., evt.webhook.catalog.item_created)"""
        # For domain events, just use the base publisher
        return await self.publish_event(
            event_type=event_type,
            payload=payload,
            correlation_id=correlation_id,
            metadata=metadata,
        )
