# services/credit-service/src/events/publishers.py
"""Event publishers for credit service."""

from typing import Dict, Any, Optional
from uuid import UUID
from decimal import Decimal

from shared.events.base_publisher import DomainEventPublisher
from shared.events.context import EventContextManager


class CreditEventPublisher(DomainEventPublisher):
    """Publisher for credit domain events"""
    
    def __init__(self, jetstream_wrapper, logger):
        super().__init__(
            jetstream_wrapper=jetstream_wrapper,
            domain="credit",
            logger=logger
        )
    
    async def publish_credits_recharged(
        self,
        merchant_id: UUID,
        amount: Decimal,
        new_balance: Decimal,
        source: str,
        reference_type: str,
        reference_id: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish credits recharged event"""
        payload = {
            "merchant_id": str(merchant_id),
            "amount": float(amount),
            "new_balance": float(new_balance),
            "source": source,
            "reference_type": reference_type,
            "reference_id": reference_id
        }
        
        if metadata:
            payload.update(metadata)
        
        return await self.publish_event_response(
            event_type="evt.credits.recharged",
            payload=payload,
            correlation_id=correlation_id,
            idempotency_key=f"recharge_{merchant_id}_{reference_id}"
        )
    
    async def publish_credits_refunded(
        self,
        merchant_id: UUID,
        amount: Decimal,
        new_balance: Decimal,
        original_reference_id: str,
        reason: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish credits refunded event"""
        payload = {
            "merchant_id": str(merchant_id),
            "amount": float(amount),
            "new_balance": float(new_balance),
            "original_reference_id": original_reference_id,
            "reason": reason
        }
        
        return await self.publish_event_response(
            event_type="evt.credits.refunded",
            payload=payload,
            correlation_id=correlation_id,
            idempotency_key=f"refund_{merchant_id}_{original_reference_id}"
        )
    
    async def publish_credits_adjusted(
        self,
        merchant_id: UUID,
        amount: Decimal,
        new_balance: Decimal,
        admin_id: str,
        reason: str,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish credits adjusted event"""
        payload = {
            "merchant_id": str(merchant_id),
            "amount": float(amount),
            "new_balance": float(new_balance),
            "admin_id": admin_id,
            "reason": reason
        }
        
        return await self.publish_event_response(
            event_type="evt.credits.adjusted",
            payload=payload,
            correlation_id=correlation_id,
            idempotency_key=f"adjust_{merchant_id}_{admin_id}"
        )
    
    async def publish_low_balance_reached(
        self,
        merchant_id: UUID,
        balance: Decimal,
        threshold: Decimal,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish low balance reached event"""
        payload = {
            "merchant_id": str(merchant_id),
            "balance": float(balance),
            "threshold": float(threshold)
        }
        
        return await self.publish_event_response(
            event_type="evt.credits.low_balance_reached",
            payload=payload,
            correlation_id=correlation_id
        )
    
    async def publish_balance_restored(
        self,
        merchant_id: UUID,
        balance: Decimal,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish balance restored event"""
        payload = {
            "merchant_id": str(merchant_id),
            "balance": float(balance)
        }
        
        return await self.publish_event_response(
            event_type="evt.credits.balance_restored",
            payload=payload,
            correlation_id=correlation_id
        )
    
    async def publish_balance_exhausted(
        self,
        merchant_id: UUID,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish balance exhausted event"""
        payload = {
            "merchant_id": str(merchant_id)
        }
        
        return await self.publish_event_response(
            event_type="evt.credits.balance_exhausted",
            payload=payload,
            correlation_id=correlation_id
        )
    
    async def publish_plugin_status_changed(
        self,
        merchant_id: UUID,
        previous_status: str,
        current_status: str,
        reason: str,
        balance: Decimal,
        correlation_id: Optional[str] = None
    ) -> str:
        """Publish plugin status changed event"""
        payload = {
            "merchant_id": str(merchant_id),
            "previous_status": previous_status,
            "current_status": current_status,
            "reason": reason,
            "balance": float(balance),
            "timestamp": EventContextManager.get_current_timestamp().isoformat()
        }
        
        return await self.publish_event_response(
            event_type="evt.credits.plugin_status_changed",
            payload=payload,
            correlation_id=correlation_id
        )