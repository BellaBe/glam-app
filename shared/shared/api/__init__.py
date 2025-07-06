# -------------------------------
# shared/api/__init__.py
# -------------------------------

"""
Unified API response models and utilities for glam-app microservices.

This module provides a single, consistent approach to API responses
across all services.
"""

from .models import (
    # Core models
    ApiResponse,
    Meta,
    Pagination,
    Links,
    ErrorDetail,
    T,  # Generic type
)

from .responses import (
    # Response helpers
    create_response,
    success_response,
    error_response,
    paginated_response,
)

from .dependencies import (
    # FastAPI dependencies
    PaginationDep,
    RequestContextDep,
    CorrelationIdDep,  # Re-exported from correlation
)

from .middleware import (
    # Middleware
    APIMiddleware,
    setup_middleware,
)

from .correlation import (
    # Correlation utilities
    get_correlation_id,
    set_correlation_context,
    get_correlation_context,
    add_correlation_header,
    add_correlation_to_event,
    extract_correlation_from_event,
)

__all__ = [
    # Models
    "ApiResponse",
    "Meta",
    "Pagination",
    "Links",
    "ErrorDetail",
    "T",
    
    # Response helpers
    "create_response",
    "success_response",
    "error_response",
    "paginated_response",
    
    # Dependencies
    "PaginationDep",
    "RequestContextDep",
    "CorrelationIdDep",
    
    # Correlation
    "get_correlation_id",
    "set_correlation_context",
    "get_correlation_context",
    "add_correlation_header",
    "add_correlation_to_event",
    "extract_correlation_from_event",
    
    # Middleware
    "APIMiddleware",
    "setup_middleware",
]