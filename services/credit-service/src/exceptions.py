# File: services/credits/src/exceptions.py

from shared.utils.exceptions import DomainError


class CreditAccountNotFoundError(DomainError):
    """Credit account not found"""

    code = "CREDIT_ACCOUNT_NOT_FOUND"
    status = 404

    def __init__(self, merchant_id: str):
        super().__init__(
            message=f"Credit account not found for merchant {merchant_id}",
            details={"merchant_id": merchant_id},
        )


class InsufficientCreditsError(DomainError):
    """Insufficient credits for operation"""

    code = "INSUFFICIENT_CREDITS"
    status = 400

    def __init__(self, merchant_id: str, balance: int, required: int):
        super().__init__(
            message=f"Insufficient credits. Balance: {balance}, Required: {required}",
            details={
                "merchant_id": merchant_id,
                "current_balance": balance,
                "required_amount": required,
            },
        )


class DuplicateTransactionError(DomainError):
    """Duplicate transaction attempted"""

    code = "DUPLICATE_TRANSACTION"
    status = 409

    def __init__(self, reference_type: str, reference_id: str):
        super().__init__(
            message=f"Transaction already processed: {reference_type}:{reference_id}",
            details={"reference_type": reference_type, "reference_id": reference_id},
        )
