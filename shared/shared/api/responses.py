# shared/api/responses.py
from typing import Any

from shared.api.dependencies import RequestContext

from .models import ApiResponse, ErrorDetail, Links, Meta, Pagination, T


def create_response(
    data: T | None = None,
    error: ErrorDetail | None = None,
    correlation_id: str | None = None,
    pagination: Pagination | None = None,
    links: Links | None = None,
) -> ApiResponse[T]:
    meta = Meta(correlation_id=correlation_id)
    return ApiResponse(data=data, error=error, meta=meta, pagination=pagination, links=links)


def success_response(
    data: T,
    correlation_id: str | None = None,
    links: Links | None = None,
) -> ApiResponse[T]:
    return create_response(data=data, correlation_id=correlation_id, links=links)


def error_response(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> ApiResponse[None]:
    error = ErrorDetail(code=code, message=message, details=details)
    return create_response(error=error, correlation_id=correlation_id)


def paginated_response_ctx(
    data: list[T],
    page: int,
    limit: int,
    total: int,
    ctx: RequestContext,
    **extra_query_params: Any,
) -> ApiResponse[list[T]]:
    """
    Build a paginated response using RequestContext for safe base_path and current query params.
    - Returns RELATIVE links (path + query) only.
    - Preserves current filters from ctx.query_params and merges any overrides in extra_query_params.
    """
    pagination = Pagination.create(page, limit, total)

    merged_qs = {**ctx.query_params, **extra_query_params}
    merged_qs = {k: v for k, v in merged_qs.items() if v is not None}

    for k in ("page", "limit"):
        merged_qs.pop(k, None)

    links = Links.create_paginated(ctx.base_path, page, limit, pagination.pages, **merged_qs)
    return create_response(data=data, correlation_id=ctx.correlation_id, pagination=pagination, links=links)
