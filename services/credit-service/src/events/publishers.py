# services/credit-service/src/events/publishers.py
from shared.api.correlation import get_correlation_context
from shared.messaging.publisher import Publisher

from ..schemas.events import (
    CreditsConsumedPayload,
    CreditsExhaustedPayload,
    CreditsGrantedPayload,
    CreditsInsufficientPayload,
    CreditsLowBalancePayload,
)


class CreditEventPublisher(Publisher):
    """Publish credit events"""

    @property
    def service_name(self) -> str:
        return "credit-service"

    async def credits_granted(self, data: dict) -> str:
        """Publish credits granted event"""
        payload = CreditsGrantedPayload(
            merchant_id=data["merchant_id"],
            amount=data["amount"],
            balance=data["balance"],
            reference_type=data["reference_type"],
            reference_id=data["reference_id"],
            platform_name=data["platform_name"],
        )

        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.credits.granted.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
        )

    async def credits_consumed(self, data: dict) -> str:
        """Publish credits consumed event"""
        payload = CreditsConsumedPayload(
            merchant_id=data["merchant_id"],
            amount=data["amount"],
            balance=data["balance"],
            reference_type=data["reference_type"],
            reference_id=data["reference_id"],
            platform_name=data["platform_name"],
        )

        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.credits.consumed.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
        )

    async def credits_insufficient(self, data: dict) -> str:
        """Publish insufficient credits event"""
        payload = CreditsInsufficientPayload(
            merchant_id=data["merchant_id"],
            attempted_amount=data["attempted_amount"],
            balance=data["balance"],
            platform_name=data["platform_name"],
        )

        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.credits.insufficient.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
        )

    async def credits_low_balance(self, data: dict) -> str:
        """Publish low balance warning"""
        payload = CreditsLowBalancePayload(
            merchant_id=data["merchant_id"],
            balance=data["balance"],
            threshold=data["threshold"],
            platform_name=data["platform_name"],
        )

        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.credits.low_balance.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
        )

    async def credits_exhausted(self, data: dict) -> str:
        """Publish credits exhausted event"""
        payload = CreditsExhaustedPayload(merchant_id=data["merchant_id"], platform_name=data["platform_name"])

        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.credits.exhausted.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
        )
