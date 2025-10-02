from shared.messaging.jetstream_client import JetStreamClient
from shared.messaging.listener import Listener
from shared.utils.logger import ServiceLogger

from ..services.merchant_service import MerchantService


class AppUninstalledListener(Listener):
    """Listener for app uninstalled webhook events"""

    @property
    def subject(self) -> str:
        return "evt.webhook.app.uninstalled.v1"

    @property
    def queue_group(self) -> str:
        return "merchant-uninstall"

    @property
    def service_name(self) -> str:
        return "merchant-service"

    def __init__(self, js_client: JetStreamClient, service: MerchantService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.service = service

    async def on_message(self, data: dict) -> None:
        """Handle app uninstalled event"""
        try:
            domain = data.get("domain")
            uninstall_reason = data.get("uninstall_reason")

            if not domain:
                self.logger.exception("Missing domain in uninstall event", extra={"data": data})
                return

            self.logger.info(
                f"Processing app uninstall for {domain}",
                extra={"domain": domain, "uninstall_reason": uninstall_reason},
            )

            await self.service.handle_app_uninstalled(domain, uninstall_reason)

        except Exception as e:
            self.logger.exception(f"Failed to process app uninstall: {e}", exc_info=True, extra={"data": data})
            raise  # NACK for retry
