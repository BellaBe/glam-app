# services/credit-service/src/exceptions.py
"""
Credit service exceptions using shared error classes.

All exceptions are re-exported from shared.errors for consistency
across the platform.
"""

# Re-export all shared exceptions
from shared.errors import (
    # Base exceptions
    CreditServiceError,
    BusinessError,
    ValidationError,
    NotFoundError,
    ConflictError,
    
    # HTTP exceptions
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    InternalServerError,
    ServiceUnavailableError,
    
    # Database exceptions
    DatabaseError,
    IntegrityError,
    
    # External service exceptions
    ExternalServiceError,
    RateLimitError,
)

# Credit-specific exceptions
class InsufficientCreditsError(BusinessError):
    """Raised when merchant has insufficient credits"""
    pass


class InvalidCreditAmountError(ValidationError):
    """Raised when credit amount is invalid"""
    pass


class DuplicateTransactionError(ConflictError):
    """Raised when attempting to create duplicate transaction"""
    pass


class AccountNotFoundError(NotFoundError):
    """Raised when credit account is not found"""
    pass


class TransactionNotFoundError(NotFoundError):
    """Raised when transaction is not found"""
    pass


class BalanceCalculationError(BusinessError):
    """Raised when balance calculation fails"""
    pass


class ThresholdConfigurationError(ValidationError):
    """Raised when threshold configuration is invalid"""
    pass


class PluginStatusError(BusinessError):
    """Raised when plugin status cannot be determined"""
    pass


# Export all exceptions
__all__ = [
    # Shared exceptions
    "CreditServiceError",
    "BusinessError", 
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "BadRequestError",
    "UnauthorizedError", 
    "ForbiddenError",
    "InternalServerError",
    "ServiceUnavailableError",
    "DatabaseError",
    "IntegrityError",
    "ExternalServiceError",
    "RateLimitError",
    
    # Credit-specific exceptions
    "InsufficientCreditsError",
    "InvalidCreditAmountError", 
    "DuplicateTransactionError",
    "AccountNotFoundError",
    "TransactionNotFoundError",
    "BalanceCalculationError",
    "ThresholdConfigurationError",
    "PluginStatusError",
]