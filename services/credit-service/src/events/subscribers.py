# services/credit-service/src/events/subscribers.py
from shared.events.base_subscriber import DomainEventSubscriber
from shared.events.credit.types import CreditEvents
from uuid import UUID


class OrderUpdatedSubscriber(DomainEventSubscriber):

    @property
    def subject(self) -> str:
        return CreditEvents.ORDER_UPDATED

    @property
    def subject(self) -> str:
        return CreditEvents.ORDER_UPDATED

    @property
    def durable_name(self) -> str:
        return "credit-order-updated"

    async def on_event(self, event: dict, headers=None):
        # Type-safe keys - IDE shows valid options, mypy catches typos
        credit_transaction_service = self.get_dependency("credit_transaction_service")

        payload = event.get("payload", {})
        merchant_id = UUID(payload["merchant_id"])
        order_items = payload.get("order_items", [])

        await credit_transaction_service.process_order_paid(
            merchant_id=merchant_id, order_items=order_items
        )


class TrialCreditsSubscriber(DomainEventSubscriber):

    @property
    def subject(self) -> str:
        return CreditEvents.ACCOUNT_CREATED

    @property
    def subject(self) -> str:
        return CreditEvents.ACCOUNT_CREATED

    @property
    def durable_name(self) -> str:
        return "credit-trial-credits"

    async def on_event(self, event: dict, headers=None):
        credit_transaction_service = self.get_dependency("credit_transaction_service")

        payload = event.get("payload", {})
        trial_id = UUID(payload["trial_id"])
        merchant_id = UUID(payload["merchant_id"])
        credits_to_use = int(payload["credits_to_use"])

        from ..services.credit_transaction_service import Trial

        trial = Trial(
            trial_id=trial_id, merchant_id=merchant_id, credits_to_use=credits_to_use
        )
        await credit_transaction_service.process_trial_credits(trial=trial)


class SubscriptionSubscriber(DomainEventSubscriber):

    @property
    def subject(self) -> str:
        return CreditEvents.SUBSCRIPTION_RENEWED

    @property
    def subject(self) -> str:
        return CreditEvents.SUBSCRIPTION_RENEWED

    @property
    def durable_name(self) -> str:
        return "credit-subscription-renewed"

    async def on_event(self, event: dict, headers=None):
        credit_transaction_service = self.get_dependency("credit_transaction_service")

        payload = event.get("payload", {})
        subscription_id = UUID(payload["subscription_id"])
        merchant_id = UUID(payload["merchant_id"])
        credits_used = int(payload["credits_used"])

        from ..services.credit_transaction_service import Subscription

        subscription = Subscription(
            id=subscription_id, merchant_id=merchant_id, credits_used=credits_used
        )
        await credit_transaction_service.process_subscription(subscription=subscription)


class MerchantCreatedSubscriber(DomainEventSubscriber):

    @property
    def subject(self) -> str:
        return CreditEvents.MERCHANT_CREATED

    @property
    def subject(self) -> str:
        return CreditEvents.MERCHANT_CREATED

    @property
    def durable_name(self) -> str:
        return "credit-merchant-created"

    async def on_event(self, event: dict, headers=None):
        credit_service = self.get_dependency("credit_service")

        payload = event.get("payload", {})
        merchant_id = UUID(payload["merchant_id"])
        await credit_service.create_credit(merchant_id=merchant_id)
