
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

from .base import GlamBaseError, InfrastructureError, DomainError

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    
    This matches the structure expected by clients and is used
    across all services for consistency.
    """
    
    error: Dict[str, Any]
    
    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        *,
        trace_id: Optional[str] = None,
        include_details: bool = True
    ) -> "ErrorResponse":
        """
        Create an ErrorResponse from any exception.
        
        Args:
            exc: The exception to convert
            trace_id: Optional trace ID for correlation
            include_details: Whether to include detailed error information
            
        Returns:
            ErrorResponse instance
        """
        error_dict = {}
        
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
                    "trace_id": trace_id
                }
            )
        
        # Add trace ID if provided
        if trace_id:
            error_dict["trace_id"] = trace_id
        
        # Remove details in production if requested
        if not include_details and "details" in error_dict:
            error_dict.pop("details", None)
        
        return cls(error=error_dict), status


def create_error_response(
    code: str,
    message: str,
    *,
    status: int = 500,
    details: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> tuple[ErrorResponse, int]:
    """
    Create a standardized error response.
    
    Args:
        code: Error code (e.g., "VALIDATION_ERROR")
        message: Human-readable error message
        status: HTTP status code
        details: Additional error context
        trace_id: Request trace ID for correlation
        
    Returns:
        Tuple of (ErrorResponse, status_code)
    """
    error_dict = {
        "code": code,
        "message": message
    }
    
    if details:
        error_dict["details"] = details
    
    if trace_id:
        error_dict["trace_id"] = trace_id
    
    return ErrorResponse(error=error_dict), status


def exception_to_error_response(
    exc: Exception,
    *,
    trace_id: Optional[str] = None,
    include_details: bool = True,
    log_traceback: bool = True
) -> tuple[ErrorResponse, int]:
    """
    Convert any exception to a standardized error response.
    
    This is the main function to use in exception handlers.
    
    Args:
        exc: The exception to convert
        trace_id: Request trace ID
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
                "trace_id": trace_id
            }
        )
    
    return ErrorResponse.from_exception(
        exc,
        trace_id=trace_id,
        include_details=include_details
    )
