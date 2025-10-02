# billing-service/src/events/publishers.py
from datetime import UTC, datetime

from shared.messaging.events.base import MerchantIdentifiers
from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects

from ..schemas.billing import CreditsPurchasedPayload, TrialStartedPayload


class BillingEventPublisher(Publisher):
    """Publisher for billing domain events"""

    @property
    def service_name(self) -> str:
        return "billing-service"

    async def billing_record_created(self, billing_record) -> str:
        """Publish billing record created event"""
        identifiers = MerchantIdentifiers(
            merchant_id=billing_record.merchant_id,
            platform_name=billing_record.platform_name,
            platform_shop_id=billing_record.platform_shop_id,
            domain=billing_record.domain,
        )
        payload = {
            "identifiers": identifiers.model_dump(mode="json"),
            "billing_record_id": str(billing_record.id),
            "plan": billing_record.plan,
            "status": billing_record.status,
            "trial_start_date": billing_record.trial_start_date.isoformat()
            if billing_record.trial_start_date
            else None,
            "trial_end_date": billing_record.trial_end_date.isoformat() if billing_record.trial_end_date else None,
            "next_billing_date": billing_record.next_billing_date.isoformat()
            if billing_record.next_billing_date
            else None,
        }
        return await self.publish_event(subject=Subjects.BILLING_RECORD_CREATED, data=payload)

    async def trial_started(self, payload: TrialStartedPayload) -> str:
        """Publish trial started event"""
        self.logger.info(
            "Publishing trial started event",
            extra={
                "merchant_id": payload.merchant_id,
                "trial_start_date": datetime.now(UTC).isoformat(),
            },
        )
        return await self.publish_event(subject=Subjects.BILLING_TRIAL_STARTED, data=payload.model_dump(mode="json"))

    async def credits_purchased(self, payload: CreditsPurchasedPayload) -> str:
        """Publish credits purchased event"""
        self.logger.info(
            "Publishing credits purchased event",
            extra={
                "merchant_id": payload.merchant_id,
                "credits": payload.credits,
                "amount": payload.amount,
                "platform": payload.platform,
            },
        )
        return await self.publish_event(
            subject=Subjects.BILLING_CREDITS_PURCHASED, data=payload.model_dump(mode="json")
        )
