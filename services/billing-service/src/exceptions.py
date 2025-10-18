from shared.utils.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)


class BillingAccountNotFoundError(NotFoundError):
    """Raised when billing account is not found"""

    def __init__(self, message: str = "Billing account not found"):
        super().__init__(message=message, resource="billing_account")


class MerchantNotFoundError(NotFoundError):
    """Raised when merchant billing account is not found"""

    def __init__(self, message: str = "Merchant not found"):
        super().__init__(message=message, resource="merchant")


class ProductNotFoundError(NotFoundError):
    """Raised when product is not found"""

    def __init__(self, message: str = "Product not found"):
        super().__init__(message=message, resource="product")


class PaymentNotFoundError(NotFoundError):
    """Raised when payment is not found"""

    def __init__(self, message: str = "Payment not found"):
        super().__init__(message=message, resource="payment")


class TrialAlreadyActivatedError(ConflictError):
    """Raised when trial is already activated"""

    def __init__(self, message: str = "Trial already activated"):
        super().__init__(message=message, conflicting_resource="trial")


class ProductInactiveError(ValidationError):
    """Raised when product is inactive"""

    def __init__(self, message: str = "Product not available"):
        super().__init__(message=message, field="product_id")


class InvalidPlatformError(ValidationError):
    """Raised when platform is not supported"""

    def __init__(self, message: str = "Platform not supported"):
        super().__init__(message=message, field="platform")


class PlatformChargeError(Exception):
    """Raised when platform charge creation fails"""

    pass
