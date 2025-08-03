from shared.utils.exceptions import (
    NotFoundError, ValidationError, ConflictError,
    DomainError
)

class MerchantNotFoundError(NotFoundError):
    """Raised when merchant is not found"""
    def __init__(self, message: str = "Merchant not found"):
        super().__init__(message=message, resource="merchant")

class InvalidDomainError(ValidationError):
    """Raised when shop domain is invalid"""
    def __init__(self, message: str = "Invalid shop domain format"):
        super().__init__(message=message, field="shop_domain")

class ConsentViolationError(ConflictError):
    """Raised when trying to violate consent rules"""
    def __init__(self, message: str = "Cannot unset required consent"):
        super().__init__(message=message, conflicting_resource="consent")

class InvalidStatusTransitionError(DomainError):
    """Raised when status transition is invalid"""
    def __init__(self, message: str):
        super().__init__(message=message, code="INVALID_STATUS_TRANSITION")

