# services/credit-service/src/events/publishers.py
"""Event publishers for separated credit services."""


from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID

from shared.events import (
    Streams,
    DomainEventPublisher,
    EventContextManager,
    EventContext,
)
from shared.events.base_publisher import DomainEventPublisher


class CreditEventPublisher(DomainEventPublisher):
    """Publisher for credit domain events"""

    domain_stream = Streams.CREDIT
    service_name_override = "credit-service"

    def __init__(self, client, js, logger=None):
        super().__init__(client, js, logger)
        self.context_manager = EventContextManager(logger or self.logger)

    # Credit Account Events
    async def publish_credit_record_created(
        self,
        merchant_id: UUID,
        initial_balance: int,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Publish credit account created event"""
        payload = {
            "merchant_id": str(merchant_id),
            "initial_balance": float(initial_balance),
        }

        return await self.publish_event_response(
            subject="evt.credits.account.created",
            payload=payload,
            correlation_id=correlation_id,
            idempotency_key=f"account_created_{merchant_id}",
        )

    # Transaction Events
    async def publish_credits_updated(
        self,
        merchant_id: UUID,
        amount: int,
        new_balance: int,
        source: str,
        reference_type: str,
        reference_id: str,
        transaction_id: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Publish credits recharged event"""
        payload = {
            "merchant_id": str(merchant_id),
            "amount": float(amount),
            "new_balance": float(new_balance),
            "source": source,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "transaction_id": transaction_id,
        }

        if metadata:
            payload.update(metadata)

        return await self.publish_event_response(
            subject="evt.credits.recharged",
            payload=payload,
            correlation_id=correlation_id,
            idempotency_key=f"recharge_{merchant_id}_{reference_id}",
        )

    async def publish_low_balance_reached(
        self,
        merchant_id: UUID,
        balance: int,
        threshold: int,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Publish low balance reached event"""
        payload = {
            "merchant_id": str(merchant_id),
            "balance": float(balance),
            "threshold": float(threshold),
        }

        return await self.publish_event_response(
            subject="evt.credits.low_balance_reached",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def publish_balance_exhausted(
        self, merchant_id: UUID, correlation_id: Optional[str] = None
    ) -> str:
        """Publish balance exhausted event"""
        payload = {"merchant_id": str(merchant_id)}

        return await self.publish_event_response(
            subject="evt.credits.balance_exhausted",
            payload=payload,
            correlation_id=correlation_id,
        )

    async def publish_plugin_status_changed(
        self,
        merchant_id: UUID,
        previous_status: str,
        current_status: str,
        reason: str,
    ) -> str:
        """Publish plugin status changed event"""
        payload = {
            "merchant_id": str(merchant_id),
            "previous_status": previous_status,
            "current_status": current_status,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return await self.publish_event_response(
            subject="evt.credits.plugin_status_changed",
            payload=payload,
        )
