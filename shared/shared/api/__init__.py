# -------------------------------
# shared/api/__init__.py
# -------------------------------

"""
Unified API response models and utilities for glam-app microservices.

This module provides a single, consistent approach to API responses
across all services.
"""

from .debug import (
    setup_debug_handlers,
    # Debugging utilities
    setup_debug_middleware,
)
from .dependencies import (
    ClientAuthDep,
    InternalAuthDep,
    LoggerDep,
    PaginationDep,
    RequestContextDep,
    WebhookHeadersDep,
)
from .health import (
    # Health check utilities
    create_health_router,
)
from .middleware import (
    # Middleware
    APIMiddleware,
    setup_middleware,
)
from .models import (
    # Core models
    ApiResponse,
    ErrorDetail,
    Links,
    Meta,
    Pagination,
)
from .responses import (
    # Response helpers
    create_response,
    error_response,
    paginated_response,
    success_response,
)
from .validation import validate_shop_context

__all__ = [
    "ApiResponse",
    "Meta",
    "Pagination",
    "Links",
    "ErrorDetail",
    "create_response",
    "success_response",
    "error_response",
    "paginated_response",
    "ClientAuthDep",
    "InternalAuthDep",
    "LoggerDep",
    "PaginationDep",
    "RequestContextDep",
    "WebhookHeadersDep",
    "setup_debug_middleware",
    "setup_debug_handlers",
    "APIMiddleware",
    "setup_middleware",
    "create_health_router",
    "validate_shop_context",
]
