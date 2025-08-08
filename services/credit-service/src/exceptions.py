from shared.utils.exceptions import (
    GlamBaseError,
    DomainError,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError
)

class CreditServiceError(GlamBaseError):
    """Base exception for credit service"""
    pass

class InvalidDomainError(ValidationError):
    """Invalid shop domain format"""
    def __init__(self, domain: str):
        super().__init__(
            message=f"Invalid shop domain format: {domain}",
            field="shopDomain",
            value=domain
        )

class InvalidAmountError(ValidationError):
    """Invalid credit amount"""
    def __init__(self, amount: int):
        super().__init__(
            message="Amount must be positive",
            field="amount",
            value=amount
        )

class MissingHeaderError(ValidationError):
    """Missing required header"""
    def __init__(self, header: str):
        super().__init__(
            message=f"Missing {header} header",
            field=header
        )

class MerchantCreditNotFoundError(NotFoundError):
    """Merchant credit account not found"""
    def __init__(self, shop_domain: str):
        super().__init__(
            message="Merchant credit account not found",
            resource="merchant_credit",
            resource_id=shop_domain
        )

class DuplicateGrantError(ConflictError):
    """Grant already processed (for internal use)"""
    def __init__(self, external_ref: str):
        super().__init__(
            message="Grant already processed",
            conflicting_resource="credit_grant",
            current_state=external_ref
        )

