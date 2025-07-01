
# -------------------------------
# shared/errors/utils.py
# -------------------------------

"""
Utility functions for error handling and classification.

This module provides helpers for wrapping external errors,
classifying HTTP errors, and determining retry behavior.
"""

from typing import Type, Optional, Callable, TypeVar, Any
import httpx
import asyncio
from functools import wraps

from .base import (
    GlamBaseError,
    InfrastructureError,
    TimeoutError,
    ServiceUnavailableError,
    RateLimitedError,
)
from .infrastructure import UpstreamServiceError

T = TypeVar("T")


def wrap_external_error(
    error_class: Type[GlamBaseError],
    message: str,
    *,
    cause: Exception,
    **kwargs
) -> GlamBaseError:
    """
    Wrap an external exception in a domain-specific error.
    
    This preserves the original exception chain while providing
    a clean domain error for upper layers.
    
    Args:
        error_class: The error class to wrap with
        message: Human-readable error message
        cause: The original exception
        **kwargs: Additional arguments for the error class
        
    Returns:
        Instance of error_class with proper cause chain
    """
    return error_class(message, cause=cause, **kwargs)


def classify_http_error(
    exc: httpx.HTTPError,
    *,
    service_name: str = "upstream"
) -> InfrastructureError:
    """
    Classify HTTP errors into appropriate infrastructure errors.
    
    Args:
        exc: The HTTP exception to classify
        service_name: Name of the upstream service
        
    Returns:
        Appropriate InfrastructureError subclass
    """
    if isinstance(exc, httpx.TimeoutException):
        return TimeoutError(
            f"Request to {service_name} timed out",
            cause=exc,
            operation="http_request"
        )
    
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        
        if status == 429:
            # Extract retry-after if available
            retry_after = exc.response.headers.get("Retry-After")
            return RateLimitedError(
                f"Rate limited by {service_name}",
                cause=exc,
                retry_after=int(retry_after) if retry_after else None
            )
        
        if status == 503:
            return ServiceUnavailableError(
                f"{service_name} is temporarily unavailable",
                cause=exc
            )
        
        if 500 <= status < 600:
            return UpstreamServiceError(
                f"{service_name} returned {status}",
                cause=exc,
                upstream_service=service_name,
                upstream_status=status,
                endpoint=str(exc.request.url)
            )
        
        # 4xx errors - usually client errors, not retryable
        return UpstreamServiceError(
            f"{service_name} rejected request: {status}",
            cause=exc,
            upstream_service=service_name,
            upstream_status=status,
            endpoint=str(exc.request.url),
            retryable=False
        )
    
    # Generic connection errors
    return InfrastructureError(
        f"Failed to connect to {service_name}",
        cause=exc,
        service=service_name
    )


def is_retryable_error(exc: Exception) -> bool:
    """
    Determine if an error should be retried.
    
    Args:
        exc: The exception to check
        
    Returns:
        True if the error is retryable
    """
    if isinstance(exc, InfrastructureError):
        return exc.retryable
    
    # Specific exceptions that are retryable
    retryable_types = (
        asyncio.TimeoutError,
        ConnectionError,
        TimeoutError,
    )
    
    return isinstance(exc, retryable_types)


def with_error_mapping(
    mappings: dict[Type[Exception], Type[GlamBaseError]],
    *,
    default_error: Type[GlamBaseError] = InfrastructureError,
    default_message: str = "Operation failed"
):
    """
    Decorator to automatically map exceptions to domain errors.
    
    Example:
        @with_error_mapping({
            FileNotFoundError: NotFoundError,
            PermissionError: ForbiddenError,
        })
        async def read_file(path: str):
            ...
    
    Args:
        mappings: Dict mapping exception types to error classes
        default_error: Error class for unmapped exceptions
        default_message: Default message for unmapped errors
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                # Check if we have a mapping for this exception
                for exc_type, error_class in mappings.items():
                    if isinstance(exc, exc_type):
                        raise error_class(
                            str(exc) or default_message,
                            cause=exc
                        ) from exc
                
                # No mapping found - use default
                if isinstance(exc, GlamBaseError):
                    # Already our error type - let it bubble
                    raise
                
                raise default_error(
                    str(exc) or default_message,
                    cause=exc
                ) from exc
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                # Same logic as async version
                for exc_type, error_class in mappings.items():
                    if isinstance(exc, exc_type):
                        raise error_class(
                            str(exc) or default_message,
                            cause=exc
                        ) from exc
                
                if isinstance(exc, GlamBaseError):
                    raise
                
                raise default_error(
                    str(exc) or default_message,
                    cause=exc
                ) from exc
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

