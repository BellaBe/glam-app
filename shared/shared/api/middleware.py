# -------------------------------
# shared/api/middleware.py
# -------------------------------

"""Simplified API middleware."""

import time
import uuid
import logging
from typing import Callable

from fastapi import Request, Response
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException

from ..errors import GlamBaseError
from ..metrics import PrometheusMiddleware, metrics_endpoint

from .models import ErrorDetail
from .responses import error_response
from .correlation import get_correlation_id, set_correlation_context

logger = logging.getLogger(__name__)


class APIMiddleware(BaseHTTPMiddleware):
    """Unified middleware for request/response handling."""
    
    def __init__(self, app, *, service_name: str = "glam-service"):
        super().__init__(app)
        self.service_name = service_name
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate IDs
        request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        
        # Get correlation ID (this will check headers and generate if needed)
        correlation_id = get_correlation_id(request)
        
        # Store in request state for easy access in the request
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        # IMPORTANT: Set correlation context for async operations
        # This makes correlation_id available throughout the request lifecycle
        set_correlation_context(correlation_id)
        
        # Track timing
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            
            # Add standard headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Service-Name"] = self.service_name
            
            return response
            
        except Exception as exc:
            # Convert to standard error response
            error_resp = self._handle_exception(exc, request_id, correlation_id)
            
            # Determine status code
            status_code = 500
            if isinstance(exc, GlamBaseError):
                status_code = exc.status
            elif isinstance(exc, HTTPException):
                status_code = exc.status_code
            elif isinstance(exc, RequestValidationError):
                status_code = 422
            
            # Log error
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "error_code": error_resp.error.code if error_resp.error else "UNKNOWN",
                    "service": self.service_name
                }
            )
            
            response = JSONResponse(
                content=error_resp.model_dump(mode="json", exclude_none=True),
                status_code=status_code
            )
            
            # Add standard headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Service-Name"] = self.service_name
            
            return response
    
    def _handle_exception(self, exc: Exception, request_id: str, correlation_id: str):
        """Convert exception to error response."""
        
        if isinstance(exc, GlamBaseError):
            return error_response(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                request_id=request_id,
                correlation_id=correlation_id
            )
        
        elif isinstance(exc, RequestValidationError):
            validation_errors = []
            for error in exc.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                validation_errors.append({
                    "field": field_path,
                    "message": error["msg"],
                    "type": error["type"]
                })
            
            return error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"validation_errors": validation_errors},
                request_id=request_id,
                correlation_id=correlation_id
            )
        
        elif isinstance(exc, HTTPException):
            return error_response(
                code=f"HTTP_{exc.status_code}",
                message=exc.detail,
                request_id=request_id,
                correlation_id=correlation_id
            )
        
        else:
            logger.exception(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__
                }
            )
            
            return error_response(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                request_id=request_id,
                correlation_id=correlation_id
            )


def setup_middleware(
    app: FastAPI,
    *,
    service_name: str,
    enable_metrics: bool = True,
    metrics_path: str = "/metrics",
):
    """
    Set up all standard middleware for a service.
    
    This sets up middleware in the correct order:
    1. Prometheus metrics (if enabled) - captures all requests
    2. API middleware - handles responses and errors
    
    Args:
        app: FastAPI application
        service_name: Name of the service
        enable_metrics: Whether to enable Prometheus metrics
        metrics_path: Path for metrics endpoint
        debug: Whether to include error details in responses
    """
    # Add Prometheus middleware FIRST (captures all requests)
    if enable_metrics:
        app.add_middleware(PrometheusMiddleware, service_name=service_name)
        
        # Add metrics endpoint
        app.add_api_route(
            metrics_path,
            metrics_endpoint,
            methods=["GET"],
            include_in_schema=False,
            tags=["monitoring"]
        )
    
    # Add API middleware for standardized responses
    app.add_middleware(APIMiddleware, service_name=service_name)
