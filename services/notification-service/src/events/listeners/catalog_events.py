# services/notification-service/src/events/listeners/catalog_events.py
from typing import Any

from shared.messaging import Listener, Subjects
from shared.utils.exceptions import ValidationError
from shared.utils.logger import ServiceLogger
from src.events.publishers import NotificationEventPublisher
from src.services.notification_service import NotificationService


class CatalogEventsListener(Listener):
    """Handle all catalog-related events"""

    @property
    def subject(self) -> str:
        return "evt.catalog.>"

    @property
    def queue_group(self) -> str:
        return "notification-catalog-events"

    @property
    def service_name(self) -> str:
        return "notification-service"

    def __init__(
        self,
        js_client,
        notification_service: NotificationService,
        event_publisher: NotificationEventPublisher,
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.notification_service = notification_service
        self.event_publisher = event_publisher

    async def on_message(self, data: dict[str, Any]) -> None:
        """Process catalog events"""
        event_type = data.get("event_type", "")

        try:
            event_data = self._flatten_platform_data(data)

            if event_type == Subjects.CATAlOG_SYNC_STARTED:
                if event_data.get("first_sync", False):  # Only notify on first sync
                    await self._handle_sync_started(event_data, data.get("correlation_id"))
            elif event_type == Subjects.CATALOG_SYNC_COMPLETED:
                await self._handle_sync_completed(event_data, data.get("correlation_id"))
            elif event_type == Subjects.CATALOG_SYNC_FAILED:
                await self._handle_sync_failed(event_data, data.get("correlation_id"))
            else:
                self.logger.debug(f"Unhandled catalog event: {event_type}")
                return

        except ValidationError as e:
            self.logger.exception(f"Invalid {event_type} event: {e}")
        except Exception as e:
            self.logger.exception(f"Failed to process {event_type}: {e}")
            raise

    async def _handle_sync_started(self, event_data: dict, correlation_id: str):
        """Handle sync started - only for first sync"""
        event_data["_template_override"] = "sync_started"
        event_data["_priority"] = "low"

        notification = await self.notification_service.process_event(
            event_type="evt.catalog.sync.started.v1", event_data=event_data, correlation_id=correlation_id or "unknown"
        )

        await self._publish_result(notification)

    async def _handle_sync_completed(self, event_data: dict, correlation_id: str):
        """Handle sync completed"""
        # Choose template based on whether it's first sync
        if event_data.get("first_sync", False):
            template = "registration_complete"
        elif event_data.get("has_changes", False):
            template = "registration_update"
        else:
            return  # No notification if no changes

        event_data["_template_override"] = template
        event_data["_priority"] = "high"

        notification = await self.notification_service.process_event(
            event_type="evt.catalog.sync.completed.v1",
            event_data=event_data,
            correlation_id=correlation_id or "unknown",
        )

        await self._publish_result(notification)

    async def _handle_sync_failed(self, event_data: dict, correlation_id: str):
        """Handle sync failure"""
        event_data["_template_override"] = "sync_failed"
        event_data["_priority"] = "high"

        notification = await self.notification_service.process_event(
            event_type="evt.catalog.sync.failed.v1", event_data=event_data, correlation_id=correlation_id or "unknown"
        )

        await self._publish_result(notification)

    def _flatten_platform_data(self, data: dict[str, Any]) -> dict[str, Any]:
        event_data = data.get("data", {}).copy()
        if "platform" in event_data:
            platform = event_data.pop("platform")
            event_data["merchant_id"] = platform.get("merchant_id")
            event_data["platform_name"] = platform.get("platform_name")
            event_data["platform_shop_id"] = platform.get("platform_shop_id")
            event_data["shop_domain"] = platform.get("domain")
        return event_data

    async def _publish_result(self, notification):
        if notification:
            if notification.status == "sent":
                await self.event_publisher.email_sent(notification)
            else:
                await self.event_publisher.email_failed(
                    notification, error=notification.error_message or "Unknown error"
                )
