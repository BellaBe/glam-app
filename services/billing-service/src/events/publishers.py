from uuid import UUID

from shared.messaging.publisher import Publisher


class BillingEventPublisher(Publisher):
    """Publisher for billing domain events"""

    @property
    def service_name(self) -> str:
        return "billing-service"

    async def billing_record_created(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_id: str,
        platform_domain: str,
        correlation_id: str,
    ) -> str:
        """Publish billing record created event"""
        payload = {
            "merchant_id": str(merchant_id),
            "platform_name": platform_name,
            "platform_id": platform_id,
            "platform_domain": platform_domain,
        }

        return await self.publish_event(
            subject="evt.billing.record.created.v1",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def trial_activated(
        self,
        merchant_id: UUID,
        grant_amount: int,
        correlation_id: str,
    ) -> str:
        """Publish trial activated event"""
        payload = {
            "merchant_id": str(merchant_id),
            "grant_amount": grant_amount,
        }

        return await self.publish_event(
            subject="evt.billing.trial.activated.v1",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def purchase_completed(
        self,
        merchant_id: UUID,
        payment_id: UUID,
        product_id: str,
        amount: float,
        currency: str,
        metadata: dict,
        correlation_id: str,
    ) -> str:
        """Publish purchase completed event"""
        payload = {
            "merchant_id": str(merchant_id),
            "payment_id": str(payment_id),
            "product_id": product_id,
            "amount": amount,
            "currency": currency,
            "metadata": metadata,
        }

        return await self.publish_event(
            subject="evt.billing.purchase.completed.v1",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def purchase_refunded(
        self,
        merchant_id: UUID,
        payment_id: UUID,
        amount: float,
        metadata: dict,
        correlation_id: str,
    ) -> str:
        """Publish purchase refunded event"""
        payload = {
            "merchant_id": str(merchant_id),
            "payment_id": str(payment_id),
            "amount": amount,
            "metadata": metadata,
        }

        return await self.publish_event(
            subject="evt.billing.purchase.refunded.v1",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def purchase_failed(
        self,
        merchant_id: UUID,
        payment_id: UUID,
        reason: str,
        correlation_id: str,
    ) -> str:
        """Publish purchase failed event"""
        payload = {
            "merchant_id": str(merchant_id),
            "payment_id": str(payment_id),
            "reason": reason,
        }

        return await self.publish_event(
            subject="evt.billing.purchase.failed.v1",
            payload=payload,
            correlation_id=correlation_id,
        )
