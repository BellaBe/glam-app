# -------------------------------
# shared/api/responses.py
# -------------------------------

"""Response helper functions."""

import uuid
from typing import Any

from .models import ApiResponse, ErrorDetail, Links, Meta, Pagination, T


def create_response(
    data: T | None = None,
    error: ErrorDetail | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    pagination: Pagination | None = None,
    links: Links | None = None,
) -> ApiResponse[T]:
    """Create a unified API response."""
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"

    meta = Meta(request_id=request_id, correlation_id=correlation_id)

    return ApiResponse(data=data, error=error, meta=meta, pagination=pagination, links=links)


def success_response(
    data: T, request_id: str | None = None, correlation_id: str | None = None, links: Links | None = None
) -> ApiResponse[T]:
    """Create a success response."""
    return create_response(data=data, request_id=request_id, correlation_id=correlation_id, links=links)


def error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
) -> ApiResponse[None]:
    """Create an error response."""
    error = ErrorDetail(code=code, message=message, details=details)
    return create_response(error=error, request_id=request_id, correlation_id=correlation_id)


def paginated_response(
    data: list[T],
    page: int,
    limit: int,
    total: int,
    base_url: str,
    request_id: str | None = None,
    correlation_id: str | None = None,
    **query_params,
) -> ApiResponse[list[T]]:
    """Create a paginated response."""
    pagination = Pagination.create(page, limit, total)
    links = Links.create_paginated(base_url, page, limit, pagination.pages, **query_params)

    return create_response(
        data=data, request_id=request_id, correlation_id=correlation_id, pagination=pagination, links=links
    )
