# services/webhook-service/src/services/webhook_service.py
"""Main webhook processing service."""

import json
from typing import Optional, Dict, Any, Type
from uuid import UUID
from datetime import datetime, timezone

from shared.utils.logger import ServiceLogger
from shared.events import EventContextManager
from shared.errors import ValidationError, NotFoundError

from ..models.webhook_entry import WebhookEntry, WebhookSource, WebhookStatus
from ..repositories.webhook_repository import WebhookRepository
from ..events.publishers import WebhookEventPublisher
from ..handlers.base import WebhookHandler
from ..handlers.shopify import ShopifyWebhookHandler
from ..handlers.stripe import StripeWebhookHandler
from .auth_service import WebhookAuthService
from .deduplication_service import DeduplicationService
from .circuit_breaker_service import CircuitBreakerService


class WebhookService:
    """Main service for webhook processing"""

    def __init__(
        self,
        webhook_repo: WebhookRepository,
        auth_service: WebhookAuthService,
        dedup_service: DeduplicationService,
        circuit_breaker: CircuitBreakerService,
        publisher: WebhookEventPublisher,
        logger: Optional[ServiceLogger] = None,
    ):
        self.webhook_repo = webhook_repo
        self.auth_service = auth_service
        self.dedup_service = dedup_service
        self.circuit_breaker = circuit_breaker
        self.publisher = publisher
        self.logger = logger or ServiceLogger(__name__)
        self.context_manager = EventContextManager(self.logger)

        # Initialize handlers
        self.handlers: Dict[WebhookSource, WebhookHandler] = {
            WebhookSource.SHOPIFY: ShopifyWebhookHandler(logger=self.logger),
            WebhookSource.STRIPE: StripeWebhookHandler(logger=self.logger),
        }

    async def process_webhook(
        self,
        source: WebhookSource,
        headers: dict,
        body: bytes,
        topic: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process incoming webhook with full validation and deduplication

        Returns:
            Dict with processing result
        """
        start_time = datetime.now(timezone.utc)
        correlation_id = headers.get("x-correlation-id") or str(UUID())

        self.logger.info(
            "Processing webhook",
            extra={
                "source": source.value,
                "topic": topic,
                "correlation_id": correlation_id,
            },
        )

        try:
            # 1. Validate signature
            if not await self.auth_service.validate_webhook(source, body, headers):
                await self.publisher.publish_validation_failed(
                    source=source.value,
                    reason="Invalid signature",
                    topic=topic,
                    correlation_id=correlation_id,
                )
                raise ValidationError("Invalid webhook signature")

            # 2. Get handler
            handler = self.handlers.get(source)
            if not handler:
                raise ValidationError(f"No handler for source: {source}")

            # 3. Parse webhook
            parsed = json.loads(body.decode("utf-8"))
            webhook_data = handler.parse_webhook(parsed, topic, headers)

            # 4. Check deduplication
            idempotency_key = webhook_data.idempotency_key
            if await self.dedup_service.is_duplicate(idempotency_key):
                self.logger.info(
                    "Duplicate webhook detected",
                    extra={
                        "idempotency_key": idempotency_key,
                        "source": source.value,
                        "topic": webhook_data.topic,
                    },
                )
                return {"status": "duplicate", "message": "Webhook already processed"}

            # 5. Store webhook entry
            entry = await self.webhook_repo.create_entry(
                source=source,
                topic=webhook_data.topic,
                headers=headers,
                payload=parsed,
                hmac_signature=headers.get(
                    (
                        "x-shopify-hmac-sha256"
                        if source == WebhookSource.SHOPIFY
                        else "stripe-signature"
                    ),
                    "",
                ),
                idempotency_key=idempotency_key,
                merchant_id=webhook_data.merchant_id,
                merchant_domain=webhook_data.merchant_domain,
            )

            # 6. Mark as seen for deduplication
            await self.dedup_service.mark_as_seen(idempotency_key)

            # 7. Publish raw webhook received event
            await self.publisher.publish_webhook_received(
                source=source.value,
                topic=webhook_data.topic,
                merchant_id=webhook_data.merchant_id,
                merchant_domain=webhook_data.merchant_domain,
                webhook_id=str(entry.id),
                correlation_id=correlation_id,
            )

            # 8. Map to domain event
            domain_event = handler.map_to_domain_event(webhook_data)

            if domain_event:
                # 9. Check circuit breaker
                subject = domain_event.event_type
                if not await self.circuit_breaker.can_proceed(subject):
                    self.logger.warning(
                        "Circuit breaker open", extra={"subject": subject}
                    )
                    await self.webhook_repo.mark_as_failed(
                        entry.id, "Circuit breaker open"
                    )
                    raise ValidationError("Circuit breaker open")

                # 10. Publish domain event
                try:
                    await self.publisher.publish_domain_event(
                        event_type=domain_event.event_type,
                        payload=domain_event.payload,
                        correlation_id=correlation_id,
                        metadata={
                            "webhook_id": str(entry.id),
                            "source": source.value,
                            "topic": webhook_data.topic,
                        },
                    )

                    # Record success
                    await self.circuit_breaker.record_success(subject)

                except Exception as e:
                    # Record failure
                    await self.circuit_breaker.record_failure(subject)
                    raise

            # 11. Mark as processed
            await self.webhook_repo.mark_as_processed(entry.id)

            # 12. Publish processed event
            await self.publisher.publish_webhook_processed(
                entry_id=str(entry.id),
                source=source.value,
                topic=webhook_data.topic,
                event_type=domain_event.event_type if domain_event else "none",
                merchant_id=webhook_data.merchant_id,
                merchant_domain=webhook_data.merchant_domain,
                correlation_id=correlation_id,
            )

            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.info(
                "Webhook processed successfully",
                extra={
                    "entry_id": str(entry.id),
                    "source": source.value,
                    "topic": webhook_data.topic,
                    "processing_time": processing_time,
                    "correlation_id": correlation_id,
                },
            )

            return {
                "status": "processed",
                "entry_id": str(entry.id),
                "processing_time": processing_time,
            }

        except Exception as e:
            self.logger.error(
                "Failed to process webhook",
                extra={
                    "source": source.value,
                    "topic": topic,
                    "error": str(e),
                    "correlation_id": correlation_id,
                },
            )

            # Try to mark as failed if we have an entry
            if "entry" in locals():
                await self.webhook_repo.mark_as_failed(entry.id, str(e))

                await self.publisher.publish_webhook_failed(
                    entry_id=str(entry.id),
                    source=source.value,
                    topic=topic or "unknown",
                    error=str(e),
                    attempts=1,
                    correlation_id=correlation_id,
                )

            raise
