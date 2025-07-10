# services/notification-service/src/events/subscribers.py

"""Event subscribers for notification service with improved context handling."""

import time
from typing import Optional, Dict, Any
from pydantic import ValidationError

from shared.events import DomainEventSubscriber
from shared.events.notification.types import (
    NotificationCommands,
    SendEmailCommandPayload,
    SendEmailBulkCommandPayload,
)

from shared.events import EventContextManager, EventContext, EventPayload
from ..schemas import NotificationCreate
from ..services.notification_service import NotificationService


class NotificationEventSubscriber(DomainEventSubscriber):
    """Base class for notification event subscribers with standardized context handling."""

    def __init__(
        self, client, js, notification_service: NotificationService, logger=None
    ):
        super().__init__(client, js, logger)
        self.notification_service = notification_service
        self.context_manager = EventContextManager(logger)

    async def on_event(
        self, event: Dict[str, Any], headers: Optional[Dict[str, str]] = None
    ):
        """Entry point for event processing with standardized context."""
        start_time = time.time()
        context = None

        try:
            # Extract and validate context
            context = self.context_manager.extract_context(event)

            # Parse payload
            payload_data = event.get("payload", {})

            # Process event with context
            await self.process_with_context(
                EventPayload(context=context, data=payload_data)
            )

            # Log success
            duration_ms = (time.time() - start_time) * 1000
            self.context_manager.log_event_completion(
                context, success=True, duration_ms=duration_ms
            )

        except ValidationError as e:
            # Log validation error
            if context:
                self.context_manager.log_event_completion(
                    context,
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    error=e,
                )
            else:
                self.logger.error(
                    f"Validation error processing event: {e}",
                    extra={"event_id": event.get("event_id"), "errors": e.errors()},
                )
            # Return True to ACK and prevent poison message
            return True

        except Exception as e:
            # Log processing error
            if context:
                self.context_manager.log_event_completion(
                    context,
                    success=False,
                    duration_ms=(time.time() - start_time) * 1000,
                    error=e,
                )
            else:
                self.logger.error(
                    f"Failed to process event: {e}",
                    extra={"event_id": event.get("event_id")},
                    exc_info=True,
                )
            # Re-raise to trigger retry logic
            raise

    async def process_with_context(self, payload: EventPayload[Dict[str, Any]]):
        """Override in subclasses to handle specific event logic with context."""
        raise NotImplementedError


class SendEmailSubscriber(NotificationEventSubscriber):
    """Handle single email send commands."""

    @property
    def event_type(self):
        return NotificationCommands.NOTIFICATION_SEND_EMAIL

    @property
    def subject(self):
        return NotificationCommands.NOTIFICATION_SEND_EMAIL

    @property
    def durable_name(self):
        return "notification-send-email"

    async def process_with_context(self, payload: EventPayload[Dict[str, Any]]):
        """Process send email command with context."""
        # Validate payload
        payload = SendEmailCommandPayload(**payload.data)

        self.logger.info(
            "Sending single notification",
            extra={
                **payload.context.to_dict(),
                "notification_type": payload.notification_type,
                "recipient": payload.recipient.email,
                "merchant_id": str(payload.recipient.id),
            },
        )

        # Build notification create with event context
        notification_create = NotificationCreate(
            notification_type=payload.notification_type,
            merchant_id=payload.recipient.id,
            shop_domain=payload.recipient.domain,
            shop_email=payload.recipient.email,
            unsubscribe_token=payload.recipient.unsubscribe_token,
            dynamic_content=payload.recipient.dynamic_content or {},
            extra_metadata={
                "event_context": payload.context.to_dict(),
                "source_event": payload.context.event_type,
                "event_id": payload.context.event_id,
                "correlation_id": payload.context.correlation_id,
            },
        )

        # Create and send notification
        notification = await self.notification_service.create_and_send_notification(
            notification_create
        )

        self.logger.info(
            "Notification sent successfully",
            extra={
                **payload.context.to_dict(),
                "notification_id": str(notification),
            },
        )


class SendBulkEmailSubscriber(NotificationEventSubscriber):
    """Handle bulk email send commands."""

    @property
    def event_type(self):
        return NotificationCommands.NOTIFICATION_SEND_BULK

    @property
    def subject(self):
        return NotificationCommands.NOTIFICATION_SEND_BULK

    @property
    def durable_name(self):
        return "notification-send-bulk"

    async def process_with_context(self, payload: EventPayload[Dict[str, Any]]):
        """Process bulk email command with context."""
        # Validate payload
        payload = SendEmailBulkCommandPayload(**payload.data)

        self.logger.info(
            "Processing bulk email send",
            extra={
                **payload.context.to_dict(),
                "notification_type": payload.notification_type,
                "recipient_count": len(payload.recipients),
            },
        )

        # Process in batches
        batch_size = 50
        total_sent = 0
        total_failed = 0

        for i in range(0, len(payload.recipients), batch_size):
            batch = payload.recipients[i : i + batch_size]
            batch_number = i // batch_size + 1

            self.logger.info(
                f"Processing batch {batch_number}",
                extra={
                    **payload.context.to_dict(),
                    "batch_number": batch_number,
                    "batch_size": len(batch),
                },
            )

            # Process batch
            for recipient in batch:
                try:
                    notification_create = NotificationCreate(
                        merchant_id=recipient.merchant_id,
                        shop_domain=recipient.shop_domain,
                        shop_email=recipient.email,
                        unsubscribe_token=recipient.unsubscribe_token,
                        notification_type=payload.notification_type,
                        dynamic_content=recipient.dynamic_content or {},
                        extra_metadata={
                            "event_context": payload.context.to_dict(),
                            "source_event": payload.context.event_type,
                            "event_id": payload.context.event_id,
                            "correlation_id": payload.context.correlation_id,
                            "bulk_batch": batch_number,
                            "bulk_job_id": payload.context.idempotency_key,
                        },
                    )

                    await self.notification_service.create_and_send_notification(
                        notification_create
                    )
                    total_sent += 1

                except Exception as e:
                    self.logger.error(
                        f"Failed to send to recipient: {e}",
                        extra={
                            **payload.context.to_dict(),
                            "recipient_email": recipient.email,
                            "batch_number": batch_number,
                        },
                    )
                    total_failed += 1

        self.logger.info(
            "Bulk send completed",
            extra={
                **payload.context.to_dict(),
                "total_sent": total_sent,
                "total_failed": total_failed,
                "total_recipients": len(payload.recipients),
                "success_rate": (
                    total_sent / len(payload.recipients) if payload.recipients else 0
                ),
            },
        )
