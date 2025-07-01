# -------------------------------
# shared/errors/handlers.py
# -------------------------------

"""
Error handling utilities for converting exceptions to standardized responses.

This module provides functions for creating consistent error responses
across all glam-app services.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel
import traceback
import logging
import uuid

from shared.api.models import ErrorDetail, ResponseMeta

from .base import GlamBaseError, InfrastructureError, DomainError

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    
    This matches the structure expected by clients and is used
    across all services for consistency.
    """
    
    error: ErrorDetail
    
    meta: Optional[ResponseMeta] = None
    
    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        *,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        include_details: bool = True
    ) -> tuple["ErrorResponse", int]:
        """
        Create an ErrorResponse from any exception.
        
        Args:
            exc: The exception to convert
            request_id: Request ID for tracing
            correlation_id: Correlation ID for distributed tracing
            include_details: Whether to include detailed error information
            
        Returns:
            Tuple of (ErrorResponse, status_code)
        """
        error_dict: Dict[str, Any] = {}

        if isinstance(exc, GlamBaseError):
            # Our custom errors - use their structure
            error_dict = exc.to_dict()
            status = exc.status
        else:
            # Unexpected error - sanitize for production
            error_dict = {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
            status = 500
            
            # Log the full traceback for debugging
            logger.exception(
                "Unhandled exception",
                extra={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "request_id": request_id,
                    "correlation_id": correlation_id
                }
            )
        
        # Remove details in production if requested
        if not include_details and "details" in error_dict:
            error_dict.pop("details", None)
        
        error_detail = ErrorDetail(**error_dict)
        
        return cls(
            error=error_detail,
            meta=ResponseMeta(
                request_id=request_id or f"req_{uuid.uuid4().hex[:12]}",
                correlation_id=correlation_id
            )
        ), status


def create_error_response(
    code: str,
    message: str,
    *,
    status: int = 500,
    details: Optional[Dict[str, Any]] = None,
    request_id: str
) -> tuple[ErrorResponse, int]:
    """
    Create a standardized error response.
    
    Args:
        code: Error code (e.g., "VALIDATION_ERROR")
        message: Human-readable error message
        status: HTTP status code
        details: Additional error context
        request_id: Request ID for tracing
        
    Returns:
        Tuple of (ErrorResponse, status_code)
    """
    error_dict: ErrorDetail = ErrorDetail(
        code=code,
        message=message,
        details=details if details else None
    )
    meta = ResponseMeta(request_id=request_id, correlation_id=None)

    return ErrorResponse(error=error_dict, meta=meta), status


def exception_to_error_response(
    exc: Exception,
    *,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    include_details: bool = True,
    log_traceback: bool = True
) -> tuple[ErrorResponse, int]:
    """
    Convert any exception to a standardized error response.
    
    This is the main function to use in exception handlers.
    
    Args:
        exc: The exception to convert
        request_id: Request ID for tracing
        correlation_id: Correlation ID for distributed tracing
        include_details: Whether to include error details
        log_traceback: Whether to log the full traceback
        
    Returns:
        Tuple of (ErrorResponse, status_code)
    """
    if log_traceback and not isinstance(exc, GlamBaseError):
        # Log unexpected errors with full traceback
        logger.exception(
            "Converting exception to error response",
            extra={
                "error_type": type(exc).__name__,
                "request_id": request_id,
                "correlation_id": correlation_id
            }
        )
    
    return ErrorResponse.from_exception(
        exc,
        request_id=request_id,
        correlation_id=correlation_id,
        include_details=include_details
    )
