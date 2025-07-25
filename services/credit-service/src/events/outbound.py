# services/credit-service/src/events/outbound.py

"""
Events that the CREDIT SERVICE publishes (to other services)
"""

from shared.events.payloads.credit import CreditDeductedPayload


class CreditOutboundEvents:
    """Events the credit service publishes"""
    
    # Credit transaction events
    CREDIT_DEDUCTED = "credit.deducted.v1"
    CREDIT_ADDED = "credit.added.v1"
    CREDIT_REFUNDED = "credit.refunded.v1"
    
    # Balance events
    BALANCE_UPDATED = "credit.balance_updated.v1"
    LOW_BALANCE_REACHED = "credit.low_balance_reached.v1"
    BALANCE_EXHAUSTED = "credit.balance_exhausted.v1"
    
    # System events
    INSUFFICIENT_CREDITS = "credit.insufficient.v1"
    
    PAYLOAD_SCHEMAS: Dict[str, Type[BaseModel]] = {
        CREDIT_DEDUCTED: CreditDeductedPayload,
    }
