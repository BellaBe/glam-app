# -------------------------------
# shared/errors/responses.py
# -------------------------------

"""
Error handling utilities for converting exceptions to standardized responses.

This module provides functions for creating consistent error responses
across all glam-app services.
"""

from typing import Any, Dict, Optional, List, Tuple
from .models import SuccessResponse, ErrorResponse, Links, PaginationMeta, DataT, ResponseMeta, ErrorDetail
import logging
import uuid


from shared.errors import GlamBaseError

logger = logging.getLogger(__name__)


def success_response(
    data: DataT,
    *,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    links: Optional[Links] = None,
    extra_meta: Optional[Dict[str, Any]] = None
) -> SuccessResponse[DataT]:
    """
    Create a standard success response.
    
    Args:
        data: The response data
        request_id: Request ID for tracing
        correlation_id: Correlation ID for distributed tracing
        links: Optional HATEOAS links
        extra_meta: Additional metadata to include
        
    Returns:
        SuccessResponse instance
    """
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    meta = ResponseMeta(
        request_id=request_id,
        correlation_id=correlation_id
    )
    
    # Add any extra metadata
    if extra_meta:
        meta_dict = meta.model_dump()
        meta_dict.update(extra_meta)
        meta = ResponseMeta(**meta_dict)
    
    return SuccessResponse(
        data=data,
        meta=meta,
        pagination=None,  # Explicitly set to None
        links=links
    )


def error_response(
    code: str,
    message: str,
    *,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    status_code: int = 500
) -> Tuple[ErrorResponse, int]:
    """
    Create a standard error response.
    
    Args:
        code: Error code
        message: Human-readable error message
        details: Additional error context
        request_id: Request ID for tracing
        correlation_id: Correlation ID for distributed tracing
        status_code: HTTP status code
        
    Returns:
        Tuple of (ErrorResponse, status_code)
    """
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    error_detail = ErrorDetail(
        code=code,
        message=message,
        details=details
    )
    
    response = ErrorResponse(
        error=error_detail,
        meta=ResponseMeta(
            request_id=request_id,
            correlation_id=correlation_id
        )
    )
    
    return response, status_code


def paginated_response(
    data: List[DataT],
    *,
    page: int,
    limit: int,
    total: int,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    base_url: str,
    **query_params
) -> SuccessResponse[List[DataT]]:
    """
    Create a paginated success response.
    
    Args:
        data: List of items for current page
        page: Current page number
        limit: Items per page
        total: Total number of items
        request_id: Request ID for tracing
        correlation_id: Correlation ID for distributed tracing
        base_url: Base URL for pagination links
        **query_params: Additional query parameters to preserve
        
    Returns:
        SuccessResponse with pagination
    """
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    # Create pagination metadata
    pagination = PaginationMeta.from_params(page, limit, total)
    
    # Build pagination links
    def build_url(page_num: int) -> str:
        params = {**query_params, "page": page_num, "limit": limit}
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query}"
    
    links = Links(
        self=build_url(page),
        next=build_url(page + 1) if pagination.has_next else None,
        previous=build_url(page - 1) if pagination.has_previous else None,
        first=build_url(1) if pagination.pages > 0 else None,
        last=build_url(pagination.pages) if pagination.pages > 0 else None
    )
    
    return SuccessResponse(
        data=data,
        meta=ResponseMeta(
            request_id=request_id,
            correlation_id=correlation_id
        ),
        pagination=pagination,
        links=links
    )


def exception_to_error_response(
    exc: Exception,
    *,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    include_details: bool = True,
    log_traceback: bool = True
) -> Tuple[ErrorResponse, int]:
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
