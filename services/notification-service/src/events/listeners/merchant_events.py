# services/notification-service/src/events/listeners/merchant_events.py
from pydantic import ValidationError

from shared.messaging import Listener
from shared.messaging.events.base import EventEnvelope
from shared.messaging.events.merchant import MerchantCreatedPayload
from shared.utils.logger import ServiceLogger
from src.services.notification_service import NotificationService

from ..publishers import NotificationEventPublisher


class MerchantEventsListener(Listener):
    """Handle all merchant events with validation."""

    @property
    def subject(self) -> str:
        return "evt.merchant.>"

    @property
    def queue_group(self) -> str:
        return "notification-merchant"

    @property
    def service_name(self) -> str:
        return "notification-service"

    def __init__(
        self,
        js_client,
        notification_service: NotificationService,
        publisher: NotificationEventPublisher,
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.publisher = publisher

    async def on_message(self, envelope: EventEnvelope) -> None:
        """
        Route merchant events based on event_type.
        Validate data based on specific event type.
        """

        # Route by event type
        if envelope.event_type == "evt.merchant.created.v1":
            await self._handle_created(envelope)
        else:
            # Unknown merchant event - just log
            self.logger.debug(f"Ignoring {envelope.event_type}", extra={"event_id": envelope.event_id})

    async def _handle_created(self, envelope: EventEnvelope):
        """Send welcome email for new merchant."""

        # Validate the data field with specific payload type
        try:
            payload = MerchantCreatedPayload.model_validate(envelope.data)
        except ValidationError as e:
            self.logger.exception(
                "Invalid merchant.created payload", extra={"event_id": envelope.event_id, "errors": e.errors()}
            )
            return  # Don't retry bad data

        try:
            notification = await self.notification_service.process_event(
                event_type=envelope.event_type,
                data=payload,
                event_id=f"{payload.identifiers.platform_name}_{envelope.source_service}_{envelope.event_id}",
                correlation_id=envelope.correlation_id,
            )

        except AttributeError:
            raise
        except Exception:
            raise

        self.logger.info(
            "Welcome email sent",
            extra={
                "event_id": envelope.event_id,
                "merchant_id": str(payload.identifiers.merchant_id),
                "correlation_id": envelope.correlation_id,
            },
        )

        await self.publisher.email_sent(notification=notification, ctx=envelope)
