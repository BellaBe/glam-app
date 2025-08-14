# -------------------------------
# shared/errors/base.py
# -------------------------------

"""
Base error classes for the glam-app error hierarchy.

This module defines the fundamental error types that all other
errors inherit from, following a three-tier model:
1. GlamBaseError - Root of all application errors
2. InfrastructureError - External system failures
3. DomainError - Business logic violations
"""

from typing import Any, Dict, Optional


class GlamBaseError(Exception):
    """
    Base class for all glam-app errors.

    Attributes:
        code: Stable error code for clients (e.g., "VALIDATION_ERROR")
        status: HTTP status code (default 500)
        message: Human-readable error message
        details: Additional error context
        __cause__: Original exception if wrapped
    """

    code: str = "INTERNAL_ERROR"
    status: int = 500

    def __init__(
        self,
        message: str,
        *,
        code: Optional[str] = None,
        status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)

        if code is not None:
            self.code = code
        if status is not None:
            self.status = status

        self.message = message
        self.details = details or {}

        # Preserve the original exception chain
        if cause is not None:
            self.__cause__ = cause

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }

        if self.details:
            result["details"] = self.details

        return result

class InfrastructureError(GlamBaseError):
    """
    Infrastructure/external system errors.

    These are failures in external dependencies like databases,
    APIs, message queues, etc. They may be retryable.
    """

    code = "INFRASTRUCTURE_ERROR"
    status = 503  # Service Unavailable

    def __init__(
        self,
        message: str,
        *,
        service: Optional[str] = None,
        retryable: bool = True,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if service:
            self.details["service"] = service

        self.details["retryable"] = retryable
        self.retryable = retryable

class DomainError(GlamBaseError):
    """
    Domain/business logic errors.

    These represent violations of business rules or invalid
    operations within the application domain.
    """

    code = "DOMAIN_ERROR"
    status = 400  # Bad Request


# Common domain errors used across services


class ValidationError(DomainError):
    """Invalid request data or parameters."""

    code = "VALIDATION_ERROR"
    status = 422  # Unprocessable Entity

    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if field:
            self.details["field"] = field
        if value is not None:
            self.details["value"] = str(value)


class NotFoundError(DomainError):
    """Requested resource not found."""

    code = "NOT_FOUND"
    status = 404

    def __init__(
        self,
        message: str,
        *,
        resource: Optional[str] = None,
        resource_id: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if resource:
            self.details["resource"] = resource
        if resource_id is not None:
            self.details["resource_id"] = str(resource_id)


class ConflictError(DomainError):
    """Operation conflicts with current state."""

    code = "CONFLICT"
    status = 409

    def __init__(
        self,
        message: str,
        *,
        conflicting_resource: Optional[str] = None,
        current_state: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if conflicting_resource:
            self.details["conflicting_resource"] = conflicting_resource
        if current_state:
            self.details["current_state"] = current_state


class UnauthorizedError(DomainError):
    """Authentication required or failed."""

    code = "UNAUTHORIZED"
    status = 401

    def __init__(
        self,
        message: str = "Authentication required",
        *,
        auth_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if auth_type:
            self.details["auth_type"] = auth_type


class ForbiddenError(DomainError):
    """Authenticated but insufficient permissions."""

    code = "FORBIDDEN"
    status = 403

    def __init__(
        self,
        message: str = "Insufficient permissions",
        *,
        required_permission: Optional[str] = None,
        resource: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if required_permission:
            self.details["required_permission"] = required_permission
        if resource:
            self.details["resource"] = resource


class RateLimitExceededError(DomainError):
    """Too many requests."""

    code = "RATE_LIMITED"
    status = 429

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        limit: Optional[int] = None,
        window: Optional[str] = None,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if limit:
            self.details["limit"] = limit
        if window:
            self.details["window"] = window
        if retry_after:
            self.details["retry_after"] = retry_after


class ServiceUnavailableError(InfrastructureError):
    """Service temporarily unavailable."""

    code = "SERVICE_UNAVAILABLE"
    status = 503


class RequestTimeoutError(InfrastructureError):
    """Operation timed out."""

    code = "TIMEOUT"
    status = 504

    def __init__(
        self,
        message: str,
        *,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if timeout_seconds:
            self.details["timeout_seconds"] = timeout_seconds
        if operation:
            self.details["operation"] = operation


class InternalError(GlamBaseError):
    """Unexpected internal server error."""

    code = "INTERNAL_ERROR"
    status = 500

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        *,
        error_id: Optional[str] = None,
        **kwargs
    ):
        # Never expose internal details in production
        super().__init__(message, **kwargs)

        if error_id:
            self.details["error_id"] = error_id
            
            
class ConfigurationError(GlamBaseError):
    """Configuration errors in the application."""

    code = "CONFIGURATION_ERROR"
    status = 500

    def __init__(
        self,
        message: str,
        *,
        config_key: Optional[str] = None,
        expected_value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if config_key:
            self.details["config_key"] = config_key
        if expected_value is not None:
            self.details["expected_value"] = expected_value
