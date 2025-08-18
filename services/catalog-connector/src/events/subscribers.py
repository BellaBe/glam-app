# src/events/subscribers.py

from shared.events import DomainEventSubscriber

from ..schemas.sync_request import SyncFetchRequestIn


class SyncFetchRequestedSubscriber(DomainEventSubscriber):
    """Subscribe to sync fetch requests from catalog service"""

    stream_name = "CATALOG"
    subject = "sync.fetch.requested.v1"
    subject = "sync.fetch.requested.v1"
    durable_name = "connector-sync-fetch-requested"

    async def on_event(self, event: dict, headers: dict):
        """Process sync fetch request"""
        service = self.get_dependency("bulk_service")
        logger = self.get_dependency("logger")

        payload = event["payload"]
        correlation_id = event.get("correlation_id")

        logger.info(
            "Processing sync fetch request",
            extra={
                "subject": self.subject,
                "sync_id": payload.get("sync_id"),
                "shop_id": payload.get("shop_id"),
                "sync_type": payload.get("sync_type"),
                "correlation_id": correlation_id,
            },
        )

        try:
            # Parse sync request
            sync_request = SyncFetchRequestIn(**payload)

            # Start fetch operation
            await service.start_fetch_operation(sync_request, correlation_id)

        except Exception as e:
            logger.error(
                f"Failed to process sync fetch request: {e}",
                extra={
                    "sync_id": payload.get("sync_id"),
                    "correlation_id": correlation_id,
                },
            )
