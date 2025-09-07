# services/platform-connector/src/events/listeners.py
from typing import Any

from shared.api.correlation import set_correlation_context
from shared.messaging import Listener
from shared.utils.exceptions import ValidationError

from ..schemas.events import CatalogSyncRequestedPayload


class CatalogSyncRequestedListener(Listener):
    """Listen for catalog sync requests"""

    @property
    def subject(self) -> str:
        return "evt.catalog.sync.requested"

    @property
    def queue_group(self) -> str:
        return "platform-connector-sync-handler"

    @property
    def service_name(self) -> str:
        return "platform-connector"

    def __init__(self, js_client, connector_service, logger):
        super().__init__(js_client, logger)
        self.connector_service = connector_service

    async def on_message(self, data: dict[str, Any]) -> None:
        """Process catalog sync request"""
        try:
            # Validate payload
            payload = CatalogSyncRequestedPayload(**data)

            # Set correlation context from event
            if correlation_id := data.get("correlation_id"):
                set_correlation_context(correlation_id)

            self.logger.info(
                f"Received sync request for {payload.platform_name}",
                extra={
                    "correlation_id": correlation_id,
                    "sync_id": payload.sync_id,
                    "merchant_id": payload.merchant_id,
                },
            )

            # Process sync request
            await self.connector_service.process_sync_request(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                sync_id=payload.sync_id,
                correlation_id=correlation_id or "unknown",
            )

        except ValidationError as e:
            self.logger.exception(f"Invalid sync request: {e}")
            return  # ACK invalid messages

        except Exception as e:
            self.logger.exception(f"Sync request processing failed: {e}", exc_info=True)
            # Check if should retry
            if hasattr(e, "retryable") and e.retryable:
                raise  # NACK for retry
            return  # ACK non-retryable errors

    async def on_error(self, error: Exception, data: dict) -> bool:
        """Error handling with retry logic"""
        if isinstance(error, ValidationError):
            return True  # ACK - don't retry validation errors

        # Check if retryable
        if hasattr(error, "retryable") and error.retryable:
            # Check delivery count
            if self.delivery_count < self.max_deliver:
                self.logger.warning(
                    f"Retrying sync request (attempt {self.delivery_count})", extra={"error": str(error)}
                )
                return False  # NACK for retry

        # Max retries exceeded or non-retryable
        self.logger.exception(f"Sync request failed permanently: {error}", extra={"data": data})
        return True  # ACK to prevent further retries
