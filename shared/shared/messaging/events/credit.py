# shared/shared/messaging/events/credit.py

from datetime import datetime

from pydantic import Field

from shared.messaging.events.base import BaseEventPayload


class CreditBalanceLowPayload(BaseEventPayload):
    """Payload for credit balance low event"""

    balance: float = Field(..., description="Current credit balance")
    threshold: float = Field(..., description="Low balance threshold")
    email: str | None = Field(None, description="Merchant email if available")


class CreditBalanceDepletedPayload(BaseEventPayload):
    """Payload for credit balance depleted event"""

    depleted_at: datetime = Field(..., description="When balance hit zero")
    email: str | None = Field(None, description="Merchant email if available")
