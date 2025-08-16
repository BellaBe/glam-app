# billing-service/src/events/publishers.py
from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects
from ..schemas.billing import (
    TrialStartedPayload, TrialExpiredPayload, CreditsPurchasedPayload
)


class BillingEventPublisher(Publisher):
    """Publisher for billing domain events"""
    
    @property
    def service_name(self) -> str:
        return "billing-service"
    
    async def trial_started(self, payload: TrialStartedPayload) -> str:
        """Publish trial started event"""
        self.logger.info(
            "Publishing trial started event",
            extra={
                "merchant_id": payload.merchant_id,
                "trial_start_date": payload.trial_start_date.isoformat()
            }
        )
        return await self.publish_event(
            subject=Subjects.BILLING_TRIAL_STARTED,
            data=payload.model_dump(mode="json")
        )
    
    async def trial_expired(self, payload: TrialExpiredPayload) -> str:
        """Publish trial expired event"""
        self.logger.info(
            "Publishing trial expired event",
            extra={
                "merchant_id": payload.merchant_id,
                "trial_end_date": payload.trial_end_date.isoformat()
            }
        )
        return await self.publish_event(
            subject=Subjects.BILLING_TRIAL_EXPIRED,
            data=payload.model_dump(mode="json")
        )
    
    async def credits_purchased(self, payload: CreditsPurchasedPayload) -> str:
        """Publish credits purchased event"""
        self.logger.info(
            "Publishing credits purchased event",
            extra={
                "merchant_id": payload.merchant_id,
                "credits": payload.credits,
                "amount": payload.amount,
                "platform": payload.platform,
            }
        )
        return await self.publish_event(
            subject=Subjects.BILLING_CREDITS_PURCHASED,
            data=payload.model_dump(mode="json")
        )


