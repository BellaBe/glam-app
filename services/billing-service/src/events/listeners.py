from shared.messaging.jetstream_client import JetStreamClient
from shared.messaging.listener import Listener
from shared.utils.logger import ServiceLogger


class MerchantCreatedListener(Listener):
    """Listener for merchant created events"""

    @property
    def subject(self) -> str:
        return "evt.merchant.created.v1"

    @property
    def queue_group(self) -> str:
        return "billing-merchant-created"

    @property
    def service_name(self) -> str:
        return "billing-service"

    def __init__(
        self,
        js_client: JetStreamClient,
        service,  # BillingService
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.service = service

    async def on_message(self, data: dict) -> None:
        """Handle merchant created event"""
        try:
            merchant_id = data.get("merchant_id")
            platform_name = data.get("platform_name")
            platform_id = data.get("platform_id")
            platform_domain = data.get("platform_domain")
            correlation_id = data.get("correlation_id")

            if not all([merchant_id, platform_name, platform_id, platform_domain]):
                self.logger.error("Missing required fields in merchant created event", extra={"data": data})
                return

            self.logger.info(
                f"Processing merchant created for {merchant_id}",
                extra={"merchant_id": merchant_id},
            )

            await self.service.handle_merchant_created(
                merchant_id=merchant_id,
                platform_name=platform_name,
                platform_id=platform_id,
                platform_domain=platform_domain,
                correlation_id=correlation_id,
            )

        except Exception as e:
            self.logger.exception(f"Failed to process merchant created: {e}", exc_info=True, extra={"data": data})
            raise


class PurchaseUpdatedListener(Listener):
    """Listener for purchase webhook events"""

    @property
    def subject(self) -> str:
        return "evt.webhook.app.purchase_updated.v1"

    @property
    def queue_group(self) -> str:
        return "billing-purchase-updated"

    @property
    def service_name(self) -> str:
        return "billing-service"

    def __init__(
        self,
        js_client: JetStreamClient,
        service,  # BillingService
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.service = service

    async def on_message(self, data: dict) -> None:
        """Handle purchase updated webhook"""
        try:
            charge_id = data.get("charge_id")
            status = data.get("status")
            merchant_id = data.get("merchant_id")
            correlation_id = data.get("correlation_id")

            if not all([charge_id, status]):
                self.logger.error("Missing required fields in purchase updated event", extra={"data": data})
                return

            self.logger.info(
                f"Processing purchase updated for charge {charge_id}",
                extra={"charge_id": charge_id, "status": status},
            )

            await self.service.handle_purchase_updated(
                charge_id=charge_id,
                status=status,
                correlation_id=correlation_id,
            )

        except Exception as e:
            self.logger.exception(f"Failed to process purchase updated: {e}", exc_info=True, extra={"data": data})
            raise


class PurchaseRefundedListener(Listener):
    """Listener for purchase refund events"""

    @property
    def subject(self) -> str:
        return "evt.webhook.app.purchase_refunded.v1"

    @property
    def queue_group(self) -> str:
        return "billing-purchase-refunded"

    @property
    def service_name(self) -> str:
        return "billing-service"

    def __init__(
        self,
        js_client: JetStreamClient,
        service,  # BillingService
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.service = service

    async def on_message(self, data: dict) -> None:
        """Handle purchase refunded webhook"""
        try:
            charge_id = data.get("charge_id")
            merchant_id = data.get("merchant_id")
            refund_amount = data.get("refund_amount")
            correlation_id = data.get("correlation_id")

            if not all([charge_id, merchant_id]):
                self.logger.error("Missing required fields in purchase refunded event", extra={"data": data})
                return

            self.logger.info(
                f"Processing purchase refund for charge {charge_id}",
                extra={"charge_id": charge_id},
            )

            await self.service.handle_purchase_refunded(
                charge_id=charge_id,
                correlation_id=correlation_id,
            )

        except Exception as e:
            self.logger.exception(f"Failed to process purchase refunded: {e}", exc_info=True, extra={"data": data})
            raise
