# services/billing-service/src/exceptions.py
"""Billing service exceptions using shared error classes.
All exceptions are re-exported from shared.errors for consistency
across the platform.
"""

from shared.errors import (
    # Base exceptions
    DomainError,
    ValidationError,
    NotFoundError,
    ConflictError,
    
    # HTTP exceptions
    UnauthorizedError,
    ForbiddenError,
    ServiceUnavailableError,
    
    # Database exceptions
    DatabaseError,
)

class BillingServiceError(DomainError):
    """Base class for all billing service errors"""
    pass

# Billing-specific exceptions
class BillingPlanNotFoundError(NotFoundError):
    """Raised when billing plan is not found"""
    pass

class SubscriptionNotFoundError(NotFoundError):
    """Raised when subscription is not found"""
    pass

class InvalidBillingIntervalError(ValidationError):
    """Raised when billing interval is invalid"""
    pass    
class ShopifyBillingError(DomainError):
    """Raised for errors from Shopify billing API"""
    pass

class SubscriptionCreationError(DomainError):
    """Raised when subscription creation fails"""
    pass

class InvalidReturnUrlError(ValidationError):
    """Raised when return URL is invalid"""
    pass

class BillingServiceConfigError(ValidationError):
    """Raised when billing service configuration is invalid"""
    pass

# Export all exceptions
__all__ = [
    "BillingServiceError",
    "BillingPlanNotFoundError",
    "SubscriptionNotFoundError",
    "InvalidBillingIntervalError",
    "ShopifyBillingError",
    "SubscriptionCreationError",
    "InvalidReturnUrlError",
    "BillingServiceConfigError",
    # Re-export all shared exceptions
    "DomainError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    "ServiceUnavailableError",
    "DatabaseError",
]