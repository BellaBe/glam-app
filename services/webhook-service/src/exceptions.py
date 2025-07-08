# services/webhook-service/src/exceptions.py
"""
Webhook service exceptions using shared error classes.

All exceptions are re-exported from shared.errors for consistency
across the platform.
"""

from shared.errors import (
    # Base exceptions
    BaseServiceError,
    
    # Client errors (4xx)
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitError,
    
    # Server errors (5xx)
    InternalError,
    ExternalServiceError,
    DatabaseError,
    MessagingError,
    ConfigurationError,
    
    # Business logic errors
    BusinessRuleViolation,
    ResourceExhausted,
    OperationNotAllowed,
)

# Service-specific exceptions can be added here if needed
class WebhookValidationError(ValidationError):
    """Specific validation error for webhooks"""
    pass


class WebhookSignatureError(UnauthorizedError):
    """Invalid webhook signature"""
    pass


class WebhookDuplicateError(ConflictError):
    """Webhook already processed"""
    pass


__all__ = [
    # Re-exported from shared
    "BaseServiceError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "UnauthorizedError",
    "ForbiddenError",
    "RateLimitError",
    "InternalError",
    "ExternalServiceError",
    "DatabaseError",
    "MessagingError",
    "ConfigurationError",
    "BusinessRuleViolation",
    "ResourceExhausted",
    "OperationNotAllowed",
    
    # Service-specific
    "WebhookValidationError",
    "WebhookSignatureError",
    "WebhookDuplicateError",
]