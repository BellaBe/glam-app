# File: services/notification-service/src/exceptions.py
"""
Notification service exceptions using shared error classes.

All exceptions are re-exported from shared.errors for consistency
across the platform.
"""

from shared.utils.exceptions import (
    ConfigurationError,
    ConflictError,
    DomainError,
    ForbiddenError,
    GlamBaseError,
    InfrastructureError,
    InternalError,
    NotFoundError,
    RateLimitExceededError,
    RequestTimeoutError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)

__all__ = [
    "ConfigurationError",
    "ConflictError",
    "DomainError",
    "ForbiddenError",
    "GlamBaseError",
    "InfrastructureError",
    "InternalError",
    "NotFoundError",
    "RateLimitExceededError",
    "RequestTimeoutError",
    "ServiceUnavailableError",
    "UnauthorizedError",
    "ValidationError",
]
