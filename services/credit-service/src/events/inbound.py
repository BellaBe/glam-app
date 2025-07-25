# services/credit-service/src/events/inbound.py

"""
Events that the CREDIT SERVICE listens for (from other services)
"""

from shared.events.payloads.credit import CreditDeductionRequestedPayload
from shared.events.payloads.common import MerchantCreatedPayload


class CreditInboundEvents:
    """Events the credit service subscribes to"""
    
    # Credit operations from other services
    CREDIT_DEDUCTION_REQUESTED = "credit.deduction_requested.v1"
    CREDIT_ADDITION_REQUESTED = "credit.addition_requested.v1"
    
    # System events
    MERCHANT_CREATED = "merchant.created.v1"  # Setup initial credits
    
    # Usage events that consume credits
    ANALYSIS_COMPLETED = "analysis.completed.v1"  # Deduct credits
    EMAIL_SENT = "email.sent.v1"  # Might deduct credits for paid plans
    
    PAYLOAD_SCHEMAS: Dict[str, Type[BaseModel]] = {
        CREDIT_DEDUCTION_REQUESTED: CreditDeductionRequestedPayload,
        MERCHANT_CREATED: MerchantCreatedPayload,
    }
