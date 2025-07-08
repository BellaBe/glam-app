# File: services/connector-service/src/exceptions.py

"""
Connector service exceptions using shared error classes.

All exceptions are re-exported from shared.errors for consistency
across the platform.
"""

from shared.errors.base import (
    DomainError,
    ValidationError,
    ConflictError,
    RateLimitedError,
    NotFoundError,
    ExternalServiceError,
)

# Re-export base errors
__all__ = [
    'DomainError',
    'ValidationError',
    'ConflictError',
    'RateLimitedError',
    'NotFoundError',
    'ExternalServiceError',
    
    # Custom connector errors
    'StoreConnectionError',
    'ShopifyAPIError',
    'RateLimitExceededError',
    'InvalidCredentialsError',
    'StoreNotFoundError',
]

class StoreConnectionError(DomainError):
    """Base error for store connection issues."""
    
    def __init__(self, message: str, store_id: str, details: dict = None):
        super().__init__(
            message=message,
            code="STORE_CONNECTION_ERROR",
            status=503,
            details={"store_id": store_id, **(details or {})}
        )


class ShopifyAPIError(ExternalServiceError):
    """Shopify API error."""
    
    def __init__(self, message: str, status_code: int, response_body: str = None):
        super().__init__(
            service="Shopify",
            message=message,
            status_code=status_code,
            response_body=response_body
        )


class RateLimitExceededError(RateLimitedError):
    """Rate limit exceeded for Shopify API."""
    
    def __init__(self, store_id: str, retry_after: int):
        super().__init__(
            message=f"Rate limit exceeded for store {store_id}",
            retry_after=retry_after,
            limit_type="api_calls"
        )


class InvalidCredentialsError(StoreConnectionError):
    """Invalid credentials for store."""
    
    def __init__(self, store_id: str):
        super().__init__(
            message=f"Invalid credentials for store {store_id}",
            store_id=store_id,
            details={"reason": "authentication_failed"}
        )


class StoreNotFoundError(NotFoundError):
    """Store not found."""
    
    def __init__(self, store_id: str):
        super().__init__(
            message=f"Store with ID {store_id} not found.",
            resource_type="store",
            resource_id=store_id
        )
