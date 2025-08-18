# services/notification-service/src/events/listeners.py
from typing import Any

from shared.messaging.listener import Listener
from shared.messaging.subjects import Subjects
from shared.utils.exceptions import ValidationError

from ..schemas.events import (
    BillingSubscriptionExpiredPayload,
    CatalogSyncCompletedPayload,
    CreditBalanceDepletedPayload,
    CreditBalanceLowPayload,
    MerchantCreatedPayload,
)


class MerchantCreatedListener(Listener):
    """Listen for merchant created events"""

    @property
    def subject(self) -> str:
        return "evt.merchant.created.v1"

    @property
    def queue_group(self) -> str:
        return "notification-merchant-created"

    @property
    def service_name(self) -> str:
        return "notification-service"

    def __init__(self, js_client, notification_service, event_publisher, logger):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(self, data: dict[str, Any]) -> None:
        """Process merchant created event"""
        try:
            # Validate payload
            payload = MerchantCreatedPayload(**data)

            # Process notification
            notification = await self.notification_service.process_event(
                event_type=self.subject,
                event_data=payload.model_dump(),
                correlation_id=payload.correlation_id or "unknown",
            )

            # Publish result event
            if notification:
                if notification.status == "sent":
                    await self.event_publisher.email_sent(notification)
                else:
                    await self.event_publisher.email_failed(
                        notification,
                        error=notification.error_message or "Unknown error",
                    )

        except ValidationError as e:
            self.logger.error(f"Invalid merchant created event: {e}")
            # ACK invalid messages
            return
        except Exception as e:
            self.logger.error(f"Failed to process merchant created: {e}")
            raise  # NACK for retry


class CatalogSyncCompletedListener(Listener):
    """Listen for catalog sync completed events"""

    @property
    def subject(self) -> str:
        return "evt.catalog.sync.completed.v1"

    @property
    def queue_group(self) -> str:
        return "notification-catalog-sync"

    @property
    def service_name(self) -> str:
        return "notification-service"

    def __init__(self, js_client, notification_service, event_publisher, logger):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(self, data: dict[str, Any]) -> None:
        """Process catalog sync completed event"""
        try:
            payload = CatalogSyncCompletedPayload(**data)

            notification = await self.notification_service.process_event(
                event_type=self.subject,
                event_data=payload.model_dump(),
                correlation_id=payload.correlation_id or "unknown",
            )

            if notification:
                if notification.status == "sent":
                    await self.event_publisher.email_sent(notification)
                else:
                    await self.event_publisher.email_failed(
                        notification,
                        error=notification.error_message or "Unknown error",
                    )

        except ValidationError as e:
            self.logger.error(f"Invalid catalog sync event: {e}")
            return
        except Exception as e:
            self.logger.error(f"Failed to process catalog sync: {e}")
            raise


# Similar listeners for billing and credit events...
class BillingSubscriptionExpiredListener(Listener):
    """Listen for billing subscription expired events"""

    @property
    def subject(self) -> str:
        return "evt.billing.subscription.expired.v1"

    @property
    def queue_group(self) -> str:
        return "notification-billing-expired"

    @property
    def service_name(self) -> str:
        return "notification-service"

    def __init__(self, js_client, notification_service, event_publisher, logger):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(self, data: dict[str, Any]) -> None:
        """Process billing expired event"""
        try:
            payload = BillingSubscriptionExpiredPayload(**data)

            notification = await self.notification_service.process_event(
                event_type=self.subject,
                event_data=payload.model_dump(),
                correlation_id=payload.correlation_id or "unknown",
            )

            if notification:
                if notification.status == "sent":
                    await self.event_publisher.email_sent(notification)
                else:
                    await self.event_publisher.email_failed(
                        notification,
                        error=notification.error_message or "Unknown error",
                    )

        except ValidationError as e:
            self.logger.error(f"Invalid billing expired event: {e}")
            return
        except Exception as e:
            self.logger.error(f"Failed to process billing expired: {e}")
            raise


class CreditBalanceLowListener(Listener):
    """Listen for credit balance low events"""

    @property
    def subject(self) -> str:
        return Subjects.CREDIT_BALANCE_LOW.value

    @property
    def queue_group(self) -> str:
        return "notification-credit-low"

    @property
    def service_name(self) -> str:
        return "notification-service"

    def __init__(self, js_client, notification_service, event_publisher, logger):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(self, data: dict[str, Any]) -> None:
        """Process credit balance low event"""
        try:
            payload = CreditBalanceLowPayload(**data)

            notification = await self.notification_service.process_event(
                event_type=self.subject,
                event_data=payload.model_dump(),
                correlation_id=payload.correlation_id or "unknown",
            )

            if notification:
                if notification.status == "sent":
                    await self.event_publisher.email_sent(notification)
                else:
                    await self.event_publisher.email_failed(
                        notification,
                        error=notification.error_message or "Unknown error",
                    )

        except ValidationError as e:
            self.logger.error(f"Invalid credit balance low event: {e}")
            return
        except Exception as e:
            self.logger.error(f"Failed to process credit balance low: {e}")
            raise


class CreditBalanceDepletedListener(Listener):
    """Listen for credit balance depleted events"""

    @property
    def subject(self) -> str:
        return Subjects.CREDIT_BALANCE_DEPLETED.value

    @property
    def queue_group(self) -> str:
        return "notification-credit-depleted"

    @property
    def service_name(self) -> str:
        return "notification-service"

    def __init__(self, js_client, notification_service, event_publisher, logger):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(self, data: dict[str, Any]) -> None:
        """Process credit balance depleted event"""
        try:
            payload = CreditBalanceDepletedPayload(**data)

            notification = await self.notification_service.process_event(
                event_type=self.subject,
                event_data=payload.model_dump(),
                correlation_id=payload.correlation_id or "unknown",
            )

            if notification:
                if notification.status == "sent":
                    await self.event_publisher.email_sent(notification)
                else:
                    await self.event_publisher.email_failed(
                        notification,
                        error=notification.error_message or "Unknown error",
                    )

        except ValidationError as e:
            self.logger.error(f"Invalid credit depleted event: {e}")
            return
        except Exception as e:
            self.logger.error(f"Failed to process credit depleted: {e}")
            raise
