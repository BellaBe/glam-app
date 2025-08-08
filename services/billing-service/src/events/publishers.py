from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects
from ..schemas.billing import (
    TrialActivatedPayload,
    TrialExpiredPayload,
    SubscriptionChangedPayload,
    SubscriptionActivatedPayload,
    SubscriptionCancelledPayload,
    CreditsGrantPayload
)

class BillingEventPublisher(Publisher):
    """Publisher for billing domain events"""
    
    @property
    def service_name(self) -> str:
        return "billing-service"
    
    async def trial_activated(self, payload: TrialActivatedPayload) -> str:
        """Publish trial activated event"""
        return await self.publish_event(
            subject=Subjects.BILLING_TRIAL_ACTIVATED.value,
            data=payload.model_dump(),
        )
    
    async def trial_expired(self, payload: TrialExpiredPayload) -> str:
        """Publish trial expired event"""
        return await self.publish_event(
            subject=Subjects.BILLING_TRIAL_EXPIRED.value,
            data=payload.model_dump(),
        )
    
    async def subscription_changed(self, payload: SubscriptionChangedPayload) -> str:
        """Publish subscription changed event"""
        return await self.publish_event(
            subject=Subjects.BILLING_SUBSCRIPTION_CHANGED.value,
            data=payload.model_dump(),
        )
    
    async def subscription_activated(self, payload: SubscriptionActivatedPayload) -> str:
        """Publish subscription activated event"""
        return await self.publish_event(
            subject=Subjects.BILLING_SUBSCRIPTION_ACTIVATED.value,
            data=payload.model_dump(),
        )
    
    async def subscription_cancelled(self, payload: SubscriptionCancelledPayload) -> str:
        """Publish subscription cancelled event"""
        return await self.publish_event(
            subject=Subjects.BILLING_SUBSCRIPTION_CANCELLED.value,
            data=payload.model_dump(),
        )
    
    async def credits_grant(self, payload: CreditsGrantPayload) -> str:
        """Publish credits grant event"""
        return await self.publish_event(
            subject=Subjects.BILLING_CREDITS_GRANT.value,
            data=payload.model_dump(),
        )

