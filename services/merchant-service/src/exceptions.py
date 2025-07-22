# services/merchant-service/src/exceptions.py
"""Merchant service exceptions using shared error classes."""

# Re-export shared exceptions for consistency
from shared.errors import (
    # Base exceptions
    DomainError,
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
)

# Merchant-specific exception aliases
class MerchantError(DomainError):
    """Base merchant service error"""
    pass

class MerchantNotFoundError(NotFoundError):
    """Merchant not found error"""
    pass

class MerchantAlreadyExistsError(ConflictError):
    """Merchant already exists error"""
    pass

class InvalidStatusTransitionError(ValidationError):
    """Invalid status transition error"""
    pass

class OnboardingStepError(ValidationError):
    """Invalid onboarding step error"""
    pass


__all__ = [
    # Base exceptions
    "DomainError",
    "ValidationError", 
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    
    # Merchant-specific
    "MerchantError",
    "MerchantNotFoundError",
    "MerchantAlreadyExistsError", 
    "InvalidStatusTransitionError",
    "OnboardingStepError",
]