from shared.utils.exceptions import NotFoundError, DomainError


class CreditAccountNotFoundError(NotFoundError):
    def __init__(self, merchant_id: str):
        super().__init__(message=f"Credit account not found for merchant: {merchant_id}", resource="credit_account")


class InsufficientCreditsError(DomainError):
    def __init__(self, merchant_id: str, balance: int):
        super().__init__(
            message=f"Insufficient credits for merchant {merchant_id}: balance={balance}",
            code="INSUFFICIENT_CREDITS"
        )


class InvalidCreditAmountError(DomainError):
    def __init__(self, message: str):
        super().__init__(message=message, code="INVALID_CREDIT_AMOUNT")
