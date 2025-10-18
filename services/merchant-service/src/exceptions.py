from shared.utils.exceptions import ConflictError, DomainError, NotFoundError, ValidationError


class MerchantNotFoundError(NotFoundError):
    """Raised when merchant is not found"""

    def __init__(self, message: str = "Merchant not found"):
        super().__init__(message=message, resource="merchant")


class InvalidDomainError(ValidationError):
    """Raised when shop domain is invalid"""

    def __init__(self, message: str = "Invalid shop domain format"):
        super().__init__(message=message, field="domain")


class MerchantConflictError(ConflictError):
    """Raised when merchant conflict occurs"""

    def __init__(self, message: str = "Merchant conflict"):
        super().__init__(message=message, conflicting_resource="merchant")


class InvalidStatusTransitionError(DomainError):
    """Raised when status transition is invalid"""

    def __init__(self, message: str):
        super().__init__(message=message, code="INVALID_STATUS_TRANSITION")
