# -------------------------------
# shared/api/__init__.py
# -------------------------------

"""
Unified API response models and utilities for glam-app microservices.

This module provides a single, consistent approach to API responses
across all services.
"""

from .correlation import (
    add_correlation_header,
    add_correlation_to_event,
    extract_correlation_from_event,
    get_correlation_context,
    # Correlation utilities
    get_correlation_id,
    set_correlation_context,
)
from .debug import (
    setup_debug_handlers,
    # Debugging utilities
    setup_debug_middleware,
)
from .dependencies import (
    ClientAuthContext,
    ClientIpDep,
    ContentTypeDep,
    CorrelationIdDep,
    InternalAuthDep,
    LoggerDep,
    # FastAPI dependencies
    PaginationDep,
    PlatformContextDep,
    RequestContextDep,
    RequestIdDep,
    ShopDomainDep,
    ShopPlatformDep,
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
    # Models
    "ApiResponse",
    "Meta",
    "Pagination",
    "Links",
    "ErrorDetail",
    # Response helpers
    "create_response",
    "success_response",
    "error_response",
    "paginated_response",
    # Dependencies
    "PaginationDep",
    "RequestContextDep",
    "LoggerDep",
    "ClientIpDep",
    "RequestIdDep",
    "ContentTypeDep",
    "CorrelationIdDep",
    "RequestContextDep",
    "PlatformContextDep",
    "ShopDomainDep",
    "ShopPlatformDep",
    "ClientAuthContext",
    "InternalAuthDep",
    "WebhookHeadersDep",
    # Debugging
    "setup_debug_middleware",
    "setup_debug_handlers",
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
    # Health checks
    "create_health_router",
    # Validation
    "validate_shop_context",
]
