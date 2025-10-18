from uuid import UUID
from shared.messaging.events.base import MerchantIdentifiers
from shared.messaging.publisher import Publisher
from shared.messaging.subjects import Subjects


class CreditEventPublisher(Publisher):
    @property
    def service_name(self) -> str:
        return "credit-service"

    async def credits_granted(
        self,
        merchant_id: UUID,
        amount: int,
        balance: int,
        credit_type: str,
        reference_type: str,
        reference_id: str,
        platform_name: str,
        correlation_id: str
    ) -> str:
        """Emit evt.credits.granted"""
        identifiers = MerchantIdentifiers(id=merchant_id)
        payload = {
            "identifiers": identifiers.model_dump(),
            "merchant_id": str(merchant_id),
            "amount": amount,
            "balance": balance,
            "credit_type": credit_type,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "platform_name": platform_name
        }
        return await self.publish_event(
            subject="evt.credits.granted.v1",
            payload=payload,
            correlation_id=correlation_id
        )

    async def credits_consumed(
        self,
        merchant_id: UUID,
        amount: int,
        balance: int,
        credit_type: str,
        reference_type: str,
        reference_id: str,
        platform_name: str,
        correlation_id: str
    ) -> str:
        """Emit evt.credits.consumed"""
        identifiers = MerchantIdentifiers(id=merchant_id)
        payload = {
            "identifiers": identifiers.model_dump(),
            "merchant_id": str(merchant_id),
            "amount": amount,
            "balance": balance,
            "credit_type": credit_type,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "platform_name": platform_name
        }
        return await self.publish_event(
            subject="evt.credits.consumed.v1",
            payload=payload,
            correlation_id=correlation_id
        )

    async def trial_consumed(
        self,
        merchant_id: UUID,
        trial_credits_used: int,
        trial_credits_remaining: int,
        correlation_id: str
    ) -> str:
        """Emit evt.credits.trial.consumed"""
        identifiers = MerchantIdentifiers(id=merchant_id)
        payload = {
            "identifiers": identifiers.model_dump(),
            "merchant_id": str(merchant_id),
            "trial_credits_used": trial_credits_used,
            "trial_credits_remaining": trial_credits_remaining
        }
        return await self.publish_event(
            subject="evt.credits.trial.consumed.v1",
            payload=payload,
            correlation_id=correlation_id
        )

    async def trial_exhausted(
        self,
        merchant_id: UUID,
        platform_name: str,
        correlation_id: str
    ) -> str:
        """Emit evt.credits.trial.exhausted"""
        identifiers = MerchantIdentifiers(id=merchant_id)
        payload = {
            "identifiers": identifiers.model_dump(),
            "merchant_id": str(merchant_id),
            "platform_name": platform_name
        }
        return await self.publish_event(
            subject="evt.credits.trial.exhausted.v1",
            payload=payload,
            correlation_id=correlation_id
        )

    async def low_balance(
        self,
        merchant_id: UUID,
        balance: int,
        threshold: int,
        platform_name: str,
        correlation_id: str
    ) -> str:
        """Emit evt.credits.low_balance"""
        identifiers = MerchantIdentifiers(id=merchant_id)
        payload = {
            "identifiers": identifiers.model_dump(),
            "merchant_id": str(merchant_id),
            "balance": balance,
            "threshold": threshold,
            "platform_name": platform_name
        }
        return await self.publish_event(
            subject="evt.credits.low_balance.v1",
            payload=payload,
            correlation_id=correlation_id
        )

    async def exhausted(
        self,
        merchant_id: UUID,
        platform_name: str,
        correlation_id: str
    ) -> str:
        """Emit evt.credits.exhausted"""
        identifiers = MerchantIdentifiers(id=merchant_id)
        payload = {
            "identifiers": identifiers.model_dump(),
            "merchant_id": str(merchant_id),
            "platform_name": platform_name
        }
        return await self.publish_event(
            subject="evt.credits.exhausted.v1",
            payload=payload,
            correlation_id=correlation_id
        )

    async def insufficient(
        self,
        merchant_id: UUID,
        attempted_amount: int,
        balance: int,
        platform_name: str,
        correlation_id: str
    ) -> str:
        """Emit evt.credits.insufficient"""
        identifiers = MerchantIdentifiers(id=merchant_id)
        payload = {
            "identifiers": identifiers.model_dump(),
            "merchant_id": str(merchant_id),
            "attempted_amount": attempted_amount,
            "balance": balance,
            "platform_name": platform_name
        }
        return await self.publish_event(
            subject="evt.credits.insufficient.v1",
            payload=payload,
            correlation_id=correlation_id
        )