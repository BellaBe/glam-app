# services/billing-service/src/events/listeners.py
"""NATS listeners for billing service events."""

from xml.dom import ValidationErr

from shared.messaging.events.base import EventEnvelope
from shared.messaging.events.webhook import WebhookPurchaseUpdated
from shared.messaging.jetstream_client import JetStreamClient
from shared.messaging.listener import Listener
from shared.utils.logger import ServiceLogger

from ..events.publishers import BillingEventPublisher
from ..schemas.billing import MerchantCreatedPayload
from ..services.billing_service import BillingService
from ..services.purchase_service import PurchaseService


class MerchantCreatedListener(Listener):
    """Listen for merchant created events"""

    @property
    def subject(self) -> str:
        return "evt.merchant.created.v1"

    @property
    def queue_group(self) -> str:
        return "billing-merchant"

    @property
    def service_name(self) -> str:
        return "billing-service"

    def __init__(
        self,
        js_client: JetStreamClient,
        billing_service: BillingService,
        publisher: BillingEventPublisher,
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.billing_service = billing_service
        self.publisher = publisher

    async def on_message(self, envelope: EventEnvelope) -> None:
        """Handle merchant created event"""
        try:
            payload = MerchantCreatedPayload.model_validate(envelope.data)

        except ValidationErr as e:
            self.logger.exception(
                "Invalid merchant.created payload", extra={"event_id": envelope.event_id, "errors": e.errors()}
            )
            return

        try:
            billing_record = await self.billing_service.create_billing_record(payload)
            self.logger.info(
                f"Created billing record for merchant {payload.merchant_id}",
                extra={"merchant_id": payload.merchant_id, "billing_record_id": billing_record.id},
            )
        except Exception as e:
            self.logger.exception(f"Failed to create billing record: {e}", exc_info=True)
            raise

        await self.publisher.billing_record_created(billing_record.model_dump(mode="json"))


class PurchaseWebhookListener(Listener):
    """Listen for purchase webhook events"""

    @property
    def subject(self) -> str:
        return "evt.webhook.purchase_updated.v1"

    @property
    def queue_group(self) -> str:
        return "billing-purchase-webhook"

    @property
    def service_name(self) -> str:
        return "billing-service"

    def __init__(
        self,
        js_client: JetStreamClient,
        purchase_service: PurchaseService,
        publisher: BillingEventPublisher,
        logger: ServiceLogger,
    ):
        super().__init__(js_client, logger)
        self.purchase_service = purchase_service
        self.publisher = publisher

    async def on_message(self, envelope: EventEnvelope) -> None:
        """Handle purchase webhook event"""
        try:
            payload = WebhookPurchaseUpdated.model_validate(envelope.data)
        except ValidationErr as e:
            self.logger.exception(
                "Invalid webhook.purchase_updated payload", extra={"event_id": envelope.event_id, "errors": e.errors()}
            )
            return  # Don't retry bad data
        try:
            purchase = await self.purchase_service.handle_purchase_webhook(
                charge_id=payload.charge_id,
                status=payload.status,
                merchant_id=payload.merchant_id,
            )

        except AttributeError:
            raise
        except Exception:
            raise

        self.logger.info(
            f"Processed purchase webhook for purchase {purchase.id}",
            extra={"purchase_id": purchase.id, "merchant_id": payload.merchant_id},
        )
        await self.publisher.credits_purchased(purchase, envelope)
