# -------------------------------
# shared/api/responses.py
# -------------------------------

"""Response helper functions."""

from typing import Optional, Dict, Any, List, Tuple
import uuid
from .models import ApiResponse, Meta, ErrorDetail, Pagination, Links, T


def create_response(
    data: Optional[T] = None,
    error: Optional[ErrorDetail] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    pagination: Optional[Pagination] = None,
    links: Optional[Links] = None
) -> ApiResponse[T]:
    """Create a unified API response."""
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    meta = Meta(request_id=request_id, correlation_id=correlation_id)
    
    return ApiResponse(
        data=data,
        error=error,
        meta=meta,
        pagination=pagination,
        links=links
    )


def success_response(
    data: T,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    links: Optional[Links] = None
) -> ApiResponse[T]:
    """Create a success response."""
    return create_response(
        data=data,
        request_id=request_id,
        correlation_id=correlation_id,
        links=links
    )


def error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> ApiResponse[None]:
    """Create an error response."""
    error = ErrorDetail(code=code, message=message, details=details)
    return create_response(
        error=error,
        request_id=request_id,
        correlation_id=correlation_id
    )


def paginated_response(
    data: List[T],
    page: int,
    limit: int,
    total: int,
    base_url: str,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    **query_params
) -> ApiResponse[List[T]]:
    """Create a paginated response."""
    pagination = Pagination.create(page, limit, total)
    links = Links.create_paginated(base_url, page, limit, pagination.pages, **query_params)
    
    return create_response(
        data=data,
        request_id=request_id,
        correlation_id=correlation_id,
        pagination=pagination,
        links=links
    )
