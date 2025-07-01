# -------------------------------
# shared/api/middleware.py
# -------------------------------

"""
API middleware for standardized request/response handling.

This middleware integrates with the error handling layer to ensure
all responses follow the standard format.
"""

import time
import uuid
import logging
from typing import Callable, Tuple

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..errors import GlamBaseError
from .models import ErrorResponse
from .correlation import set_correlation_context, get_correlation_id

logger = logging.getLogger(__name__)


class APIResponseMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures all responses follow standard format.
    
    This middleware:
    - Adds request IDs to all requests
    - Adds correlation IDs for distributed tracing
    - Converts errors to standard ErrorResponse format
    - Adds standard headers to responses
    - Logs request metrics
    """
    
    def __init__(
        self,
        app: ASGIApp,
        *,
        service_name: str = "glam-service",
        include_error_details: bool = True
    ):
        super().__init__(app)
        self.service_name = service_name
        self.include_error_details = include_error_details
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:12]}"
        
        # Get or generate correlation ID
        correlation_id = get_correlation_id(request)
        
        # Store in request state
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        # Set correlation context for async operations
        set_correlation_context(correlation_id)
        
        # Track timing
        start_time = time.perf_counter()
        
        # Add standard headers to all responses
        def add_headers(response: Response):
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Service-Name"] = self.service_name
        
        try:
            response = await call_next(request)
            add_headers(response)
            return response
            
        except Exception as exc:
            # Convert to standard error response
            error_response, status_code = self._handle_exception(
                exc, request_id, correlation_id
            )
            
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
                    "error_code": error_response.error.code,
                    "service": self.service_name
                }
            )
            
            response = JSONResponse(
                content=error_response.model_dump(mode="json"),
                status_code=status_code
            )
            add_headers(response)
            return response
    
    def _handle_exception(
        self,
        exc: Exception,
        request_id: str,
        correlation_id: str
    ) -> Tuple[ErrorResponse, int]:
        """Convert exception to standard error response."""
        
        if isinstance(exc, GlamBaseError):
            # Our custom errors
            return ErrorResponse.from_exception(
                exc, 
                request_id=request_id, 
                correlation_id=correlation_id,
                include_details=self.include_error_details
            )
        
        elif isinstance(exc, RequestValidationError):
            # Pydantic validation errors
            validation_errors = []
            for error in exc.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                validation_errors.append({
                    "field": field_path,
                    "message": error["msg"],
                    "type": error["type"]
                })
            
            return ErrorResponse.from_exception(
                {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"validation_errors": validation_errors}
                },
                request_id=request_id,
                correlation_id=correlation_id,
                include_details=self.include_error_details
            )
        
        elif isinstance(exc, HTTPException):
            # FastAPI HTTP exceptions
            return ErrorResponse.from_exception(
                {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "status": exc.status_code  # Include status in the dict
                },
                request_id=request_id,
                correlation_id=correlation_id,
                include_details=self.include_error_details
            )
        
        else:
            # Unexpected errors
            logger.exception(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__
                }
            )
            
            return ErrorResponse.from_exception(
                {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"error_type": type(exc).__name__} if self.include_error_details else None
                },
                request_id=request_id,
                correlation_id=correlation_id,
                include_details=self.include_error_details
        )

def setup_api_middleware(
    app: FastAPI,
    *,
    service_name: str,
    include_error_details: bool = True
):
    """
    Set up all API middleware for a service.
    
    This combines:
    - API response standardization
    - Error handling from the errors module
    - Correlation ID support
    
    Args:
        app: FastAPI application
        service_name: Name of the service
        include_error_details: Whether to include error details
    """
    # Add our API response middleware
    app.add_middleware(
        APIResponseMiddleware,
        service_name=service_name,
        include_error_details=include_error_details
    )
    
    # Also set up error handlers from the errors module
    from ..errors.middleware import setup_exception_handlers
    setup_exception_handlers(app, include_details=include_error_details)