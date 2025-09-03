# services/notification-service/src/events/listeners.py

from shared.messaging.events.base import EventEnvelope
from shared.messaging.events.catalog import CatalogSyncCompletedPayload, CatalogSyncStartedPayload
from shared.messaging.events.credit import CreditBalanceDepletedPayload, CreditBalanceLowPayload
from shared.messaging.events.merchant import MerchantCreatedPayload
from shared.messaging.listener import Listener
from shared.messaging.subjects import Subjects


class MerchantCreatedListener(Listener[MerchantCreatedPayload]):
    """Listen for merchant created events"""

    @property
    def service_name(self) -> str:
        return "notification-service"

    @property
    def subject(self) -> str:
        return Subjects.MERCHANT_CREATED.value

    @property
    def queue_group(self) -> str:
        return "notification-merchant-created"

    @property
    def payload_class(self) -> type[MerchantCreatedPayload]:
        return MerchantCreatedPayload

    def __init__(self, js_client, notification_service, event_publisher, logger, delivery_service):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher
        self._delivery_service = delivery_service

    async def on_message(
        self, payload: MerchantCreatedPayload, envelope: EventEnvelope[MerchantCreatedPayload]
    ) -> None:
        """Process merchant created event"""
        try:
            self.logger.info(
                "Processing merchant created",
                extra={
                    "merchant_id": str(payload.platform.merchant_id),
                    "domain": payload.platform.domain,
                    "correlation_id": envelope.correlation_id,
                    "event_id": envelope.event_id,
                },
            )

            # Process notification
            notification = await self.notification_service.process_event(
                event_type="evt.merchant.created.v1",  # Use the subject
                data=payload,
                event_id=envelope.event_id,
                correlation_id=envelope.correlation_id,
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

        except Exception as e:
            self.logger.error(f"Failed to process merchant created: {e}")
            raise  # NACK for retry


class CatalogSyncStartedListener(Listener[CatalogSyncStartedPayload]):
    """Listen for catalog sync started events"""

    @property
    def service_name(self) -> str:
        return "notification-service"

    @property
    def subject(self) -> str:
        return Subjects.CATALOG_SYNC_STARTED.value

    @property
    def queue_group(self) -> str:
        return "notification-catalog-sync-started"

    @property
    def payload_class(self) -> type[CatalogSyncStartedPayload]:
        return CatalogSyncStartedPayload

    def __init__(
        self,
        js_client,
        notification_service,
        delivery_service,
        event_publisher,
        logger,
    ):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher
        self.delivery_service = delivery_service

    async def on_message(
        self, payload: CatalogSyncStartedPayload, envelope: EventEnvelope[CatalogSyncStartedPayload]
    ) -> None:
        """Process catalog sync started - typically no email for this"""
        self.logger.info(
            "Catalog sync started",
            extra={
                "merchant_id": str(payload.platform.merchant_id),
                "sync_id": str(payload.sync_id),
                "total_items": payload.total_items,
                "correlation_id": envelope.correlation_id,
            },
        )


class CatalogSyncCompletedListener(Listener[CatalogSyncCompletedPayload]):
    """Listen for catalog sync completed events"""

    @property
    def service_name(self) -> str:
        return "notification-service"

    @property
    def subject(self) -> str:
        return Subjects.CATALOG_SYNC_COMPLETED.value

    @property
    def queue_group(self) -> str:
        return "notification-catalog-sync-completed"

    @property
    def payload_class(self) -> type[CatalogSyncCompletedPayload]:
        return CatalogSyncCompletedPayload

    def __init__(self, js_client, notification_service, event_publisher, logger):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(
        self, payload: CatalogSyncCompletedPayload, envelope: EventEnvelope[CatalogSyncCompletedPayload]
    ) -> None:
        """Process catalog sync completed event"""
        try:
            self.logger.info(
                "Processing catalog sync completed",
                extra={
                    "merchant_id": str(payload.platform.merchant_id),
                    "sync_id": str(payload.sync_id),
                    "first_sync": payload.first_sync,
                    "has_changes": payload.has_changes,
                    "correlation_id": envelope.correlation_id,
                },
            )

            # Only send notification for first sync or significant changes
            if payload.first_sync or payload.has_changes:
                notification = await self.notification_service.process_event(
                    event_type=envelope.event_type,
                    data=payload,
                    event_id=envelope.event_id,
                    correlation_id=envelope.correlation_id,
                )

                if notification:
                    if notification.status == "sent":
                        await self.event_publisher.email_sent(notification)
                    else:
                        await self.event_publisher.email_failed(
                            notification,
                            error=notification.error_message or "Unknown error",
                        )

        except Exception as e:
            self.logger.error(f"Failed to process catalog sync completed: {e}")
            raise  # NACK for retry


class CreditBalanceLowListener(Listener[CreditBalanceLowPayload]):
    """Listen for credit balance low events"""

    @property
    def service_name(self) -> str:
        return "notification-service"

    @property
    def subject(self) -> str:
        return Subjects.CREDIT_BALANCE_LOW.value

    @property
    def queue_group(self) -> str:
        return "notification-credit-balance-low"

    @property
    def payload_class(self) -> type[CreditBalanceLowPayload]:
        return CreditBalanceLowPayload

    def __init__(self, js_client, notification_service, event_publisher, logger):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(
        self, payload: CreditBalanceLowPayload, envelope: EventEnvelope[CreditBalanceLowPayload]
    ) -> None:
        """Process credit balance low event"""
        try:
            self.logger.info(
                "Processing credit balance low",
                extra={
                    "merchant_id": str(payload.platform.merchant_id),
                    "balance": payload.balance,
                    "threshold": payload.threshold,
                    "correlation_id": envelope.correlation_id,
                },
            )

            notification = await self.notification_service.process_event(
                event_type=envelope.event_type,
                data=payload,
                event_id=envelope.event_id,
                correlation_id=envelope.correlation_id,
            )

            if notification:
                if notification.status == "sent":
                    await self.event_publisher.email_sent(notification)
                else:
                    await self.event_publisher.email_failed(
                        notification,
                        error=notification.error_message or "Unknown error",
                    )

        except Exception as e:
            self.logger.error(f"Failed to process credit balance low: {e}")
            raise  # NACK for retry


class CreditBalanceDepletedListener(Listener[CreditBalanceDepletedPayload]):
    """Listen for credit balance depleted events"""

    @property
    def service_name(self) -> str:
        return "notification-service"

    @property
    def subject(self) -> str:
        return Subjects.CREDIT_BALANCE_DEPLETED.value

    @property
    def queue_group(self) -> str:
        return "notification-credit-balance-depleted"

    @property
    def payload_class(self) -> type[CreditBalanceDepletedPayload]:
        return CreditBalanceDepletedPayload

    def __init__(self, js_client, notification_service, event_publisher, logger):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(
        self, payload: CreditBalanceDepletedPayload, envelope: EventEnvelope[CreditBalanceDepletedPayload]
    ) -> None:
        """Process credit balance depleted event"""
        try:
            self.logger.info(
                "Processing credit balance depleted",
                extra={
                    "merchant_id": str(payload.platform.merchant_id),
                    "depleted_at": payload.depleted_at.isoformat(),
                    "correlation_id": envelope.correlation_id,
                },
            )

            notification = await self.notification_service.process_event(
                event_type=envelope.event_type,
                data=payload,
                event_id=envelope.event_id,
                correlation_id=envelope.correlation_id,
            )

            if notification:
                if notification.status == "sent":
                    await self.event_publisher.email_sent(notification)
                else:
                    await self.event_publisher.email_failed(
                        notification,
                        error=notification.error_message or "Unknown error",
                    )

        except Exception as e:
            self.logger.error(f"Failed to process credit balance depleted: {e}")
            raise  # NACK for retry
