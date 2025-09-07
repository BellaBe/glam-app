# shared/shared/messaging/events/credit.py

from datetime import datetime
from pydantic import Field

from shared.messaging.events.base import BaseEventPayload


class CreditBalanceGrantedPayload(BaseEventPayload):
    """Payload for credit balance granted event"""
    amount: float = Field(..., description="Amount of credits added")
    new_balance: float = Field(..., description="New credit balance after replenishment")
    email: str = Field(..., description="Merchant email")


class CreditBalanceLowPayload(BaseEventPayload):
    """Payload for credit balance low event"""
    balance: float = Field(..., description="Current credit balance")
    email: str = Field(..., description="Merchant email")


class CreditBalanceExhaustedPayload(BaseEventPayload):
    """Payload for credit balance exhausted event"""
    exhausted_at: datetime = Field(..., description="When balance hit zero")
    email: str = Field(..., description="Merchant email")
    
class CreditTrialGrantedPayload(BaseEventPayload):
    """Payload for trial credits granted event"""
    amount: float = Field(..., description="Amount of trial credits granted")
    email: str = Field(..., description="Merchant email")
    
class CreditTrialLowPayload(BaseEventPayload):
    """Payload for trial credits low event"""
    balance: float = Field(..., description="Current trial credit balance")
    email: str = Field(..., description="Merchant email")
    
class CreditTrialExhaustedPayload(BaseEventPayload):
    """Payload for trial exhausted event"""
    exhausted_at: datetime = Field(..., description="When trial was exhausted"
    )
    email: str = Field(..., description="Merchant email")
