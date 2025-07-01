# -------------------------------
# shared/errors/infrastructure.py
# -------------------------------

"""Infrastructure-specific error classes."""

from typing import Optional
from .base import InfrastructureError


class DatabaseError(InfrastructureError):
    """Database operation failed."""
    
    code = "DATABASE_ERROR"
    
    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        error_code: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, service="database", **kwargs)
        
        if operation:
            self.details["operation"] = operation
        if table:
            self.details["table"] = table
        if error_code:
            self.details["error_code"] = error_code


class RedisError(InfrastructureError):
    """Redis operation failed."""
    
    code = "REDIS_ERROR"
    
    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, service="redis", **kwargs)
        
        if operation:
            self.details["operation"] = operation
        if key:
            self.details["key"] = key


class S3Error(InfrastructureError):
    """S3 operation failed."""
    
    code = "S3_ERROR"
    
    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
        error_code: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, service="s3", **kwargs)
        
        if operation:
            self.details["operation"] = operation
        if bucket:
            self.details["bucket"] = bucket
        if key:
            self.details["key"] = key
        if error_code:
            self.details["error_code"] = error_code


class UpstreamServiceError(InfrastructureError):
    """Upstream service call failed."""
    
    code = "UPSTREAM_SERVICE_ERROR"
    
    def __init__(
        self,
        message: str,
        *,
        upstream_service: Optional[str] = None,
        upstream_status: Optional[int] = None,
        upstream_error: Optional[str] = None,
        endpoint: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, service=upstream_service, **kwargs)
        
        if upstream_status:
            self.details["upstream_status"] = upstream_status
        if upstream_error:
            self.details["upstream_error"] = upstream_error
        if endpoint:
            self.details["endpoint"] = endpoint


class CircuitOpenError(InfrastructureError):
    """Circuit breaker is open."""
    
    code = "CIRCUIT_OPEN"
    status = 503
    
    def __init__(
        self,
        message: str,
        *,
        service_name: Optional[str] = None,
        failure_count: Optional[int] = None,
        open_until: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            service=service_name,
            retryable=False,  # Don't retry when circuit is open
            **kwargs
        )
        
        if failure_count:
            self.details["failure_count"] = failure_count
        if open_until:
            self.details["open_until"] = open_until


class MessageBusError(InfrastructureError):
    """Message bus operation failed."""
    
    code = "MESSAGE_BUS_ERROR"
    
    def __init__(
        self,
        message: str,
        *,
        operation: Optional[str] = None,
        stream: Optional[str] = None,
        subject: Optional[str] = None,
        event_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, service="nats", **kwargs)
        
        if operation:
            self.details["operation"] = operation
        if stream:
            self.details["stream"] = stream
        if subject:
            self.details["subject"] = subject
        if event_type:
            self.details["event_type"] = event_type
