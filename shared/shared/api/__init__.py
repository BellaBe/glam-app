# -------------------------------
# shared/api/__init__.py
# -------------------------------

"""
Shared API response models and utilities for glam-app microservices.

This module provides standardized request/response models and utilities
for consistent API responses across all services.
"""

from .models import (
    # Response models
    SuccessResponse,
    ErrorResponse,
    PaginationMeta,
    ResponseMeta,
    ErrorDetail,
    Links,
    
    # Generic types
    DataT,
)

from .dependencies import (
    PaginationParams,
    get_pagination_params,
    get_request_id,
    RequestIdDep,
    PaginationDep,
    RequestContextDep
)

from .middleware import (
    APIResponseMiddleware,
    setup_api_middleware,
)

from .correlation import (
    get_correlation_id,
    CorrelationIdDep,
    set_correlation_context,
    get_correlation_context,
    CorrelationContext,
    add_correlation_header,
    add_correlation_to_event,
    extract_correlation_from_event,
    CorrelationLoggerAdapter,
)

from .responses import success_response, error_response, paginated_response

__all__ = [
    # Models
    "SuccessResponse",
    "ErrorResponse",
    "PaginationMeta",
    "ResponseMeta",
    "ErrorDetail",
    "Links",
    "DataT",
    
    
    # Dependencies
    "PaginationParams",
    "get_pagination_params",
    "get_request_id",
    "RequestIdDep",
    "PaginationDep",
    "RequestContextDep",
    
    # Correlation
    "get_correlation_id",
    "CorrelationIdDep",
    "set_correlation_context",
    "get_correlation_context",
    "CorrelationContext",
    "add_correlation_header",
    "add_correlation_to_event",
    "extract_correlation_from_event",
    "CorrelationLoggerAdapter",
    
    # Middleware
    "APIResponseMiddleware",
    "setup_api_middleware",
    
    # Response utilities
    "success_response",
    "error_response",
    "paginated_response",
]
