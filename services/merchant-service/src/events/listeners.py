from typing import Dict
from shared.messaging.listener import Listener
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from ..services.merchant_service import MerchantService
from ..events.publishers import MerchantEventPublisher

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
    
    def __init__(
        self,
        js_client: JetStreamClient,
        service: MerchantService,
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.service = service
    
    async def on_message(self, data: Dict) -> None:
        """Handle app uninstalled event"""
        try:
            shop_domain = data.get("shop_domain")
            uninstall_reason = data.get("uninstall_reason")
            
            if not shop_domain:
                self.logger.error("Missing shop_domain in uninstall event", extra={"data": data})
                return
            
            self.logger.info(
                f"Processing app uninstall for {shop_domain}",
                extra={
                    "shop_domain": shop_domain,
                    "uninstall_reason": uninstall_reason
                }
            )
            
            await self.service.handle_app_uninstalled(shop_domain, uninstall_reason)
            
        except Exception as e:
            self.logger.error(
                f"Failed to process app uninstall: {e}",
                exc_info=True,
                extra={"data": data}
            )
            raise  # NACK for retry

