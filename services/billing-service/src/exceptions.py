from shared.utils.exceptions import ConflictError, DomainError, NotFoundError


class TrialAlreadyUsedError(ConflictError):
    """Raised when trial has already been activated"""

    def __init__(self, merchant_id: str):
        super().__init__(message="Trial has already been activated", conflicting_resource="trial", current_state="used")
        self.merchant_id = merchant_id


class InvalidCreditPackError(DomainError):
    """Raised when invalid credit pack is selected"""

    def __init__(self, pack: str):
        super().__init__(message=f"Invalid credit pack: {pack}", code="INVALID_PACK")
        self.pack = pack


class MerchantNotFoundError(NotFoundError):
    """Raised when merchant billing record not found"""

    def __init__(self, merchant_id: str):
        super().__init__(message=f"Merchant {merchant_id} not found", resource="merchant", resource_id=merchant_id)


class PurchaseNotFoundError(NotFoundError):
    """Raised when purchase not found"""

    def __init__(self, purchase_id: str):
        super().__init__(message=f"Purchase {purchase_id} not found", resource="purchase", resource_id=purchase_id)


class PlatformCheckoutError(DomainError):
    """Raised when platform checkout creation fails"""

    def __init__(self, platform: str, error_message: str):
        super().__init__(message=f"Failed to create {platform} checkout: {error_message}", code="PLATFORM_ERROR")
        self.platform = platform
        self.error_message = error_message
