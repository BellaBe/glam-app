# services/billing-service/src/events/listeners.py
"""NATS listeners for billing service events."""
from typing import Dict
from shared.messaging.listener import Listener
from shared.messaging.jetstream_client import JetStreamClient
from shared.utils.logger import ServiceLogger
from ..schemas.billing import MerchantCreatedPayload, PurchaseWebhookPayload
from ..services.billing_service import BillingService
from ..services.purchase_service import PurchaseService


class MerchantCreatedListener(Listener):
    """Listen for merchant created events"""
    
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
        billing_service: BillingService,
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.billing_service = billing_service
    
    async def on_message(self, data: Dict) -> None:
        """Handle merchant created event"""
        try:
            print(f"Received merchant created event================: {data}")
            payload = MerchantCreatedPayload(**data)
            await self.billing_service.create_billing_record(payload.merchant_id)
        except Exception as e:
            self.logger.error(f"Failed to process merchant created: {e}")
            raise  # Will NACK for retry


class PurchaseWebhookListener(Listener):
    """Listen for purchase webhook events"""
    
    @property
    def subject(self) -> str:
        return "evt.webhook.app.purchase_updated.v1"
    
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
        logger: ServiceLogger
    ):
        super().__init__(js_client, logger)
        self.purchase_service = purchase_service
    
    async def on_message(self, data: Dict) -> None:
        """Handle purchase webhook event"""
        try:
            payload = PurchaseWebhookPayload(**data)
            await self.purchase_service.handle_purchase_webhook(
                charge_id=payload.charge_id,
                status=payload.status,
                merchant_id=payload.merchant_id
            )
        except Exception as e:
            self.logger.error(f"Failed to process purchase webhook: {e}")
            # Don't retry webhooks - they're usually duplicates
            return


