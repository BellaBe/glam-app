# -------------------------------
# shared/errors/middleware.py
# -------------------------------

"""
FastAPI middleware and exception handlers for consistent error handling.

This module provides middleware and handlers that can be used by all
services to ensure consistent error responses.
"""

import time
import uuid
import logging
from typing import Callable, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .base import GlamBaseError, ValidationError
from .handlers import exception_to_error_response

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures all errors are converted to standard format.
    
    This middleware:
    - Catches all exceptions and converts to standard error responses
    - Logs request metrics and errors
    """
    
    def __init__(
        self,
        app: ASGIApp,
        *,
        include_details: bool = True,
        log_errors: bool = True
    ):
        super().__init__(app)
        self.include_details = include_details
        self.log_errors = log_errors
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Track request timing
        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Get request_id and correlation_id from request state if available
            request_id = getattr(request.state, "request_id", None)
            correlation_id = getattr(request.state, "correlation_id", None)
            
            # Convert exception to standard error response
            error_response, status_code = exception_to_error_response(
                exc,
                request_id=request_id,
                correlation_id=correlation_id,
                include_details=self.include_details,
                log_traceback=self.log_errors
            )
            
            # Log error with context
            if self.log_errors:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    "Request failed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status": status_code,
                        "duration_ms": round(duration_ms, 2),
                        "error_code": error_response.error.code,
                    }
                )
            
            return JSONResponse(
                content=error_response.dict(),
                status_code=status_code
            )
        
        finally:
            # Always log request completion
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                }
            )


def setup_exception_handlers(
    app: FastAPI,
    *,
    include_details: bool = True
):
    """
    Set up standard exception handlers for a FastAPI app.
    
    This adds handlers for:
    - GlamBaseError (our custom errors)
    - RequestValidationError (Pydantic validation)
    - HTTPException (FastAPI HTTP errors)
    - Generic Exception (unexpected errors)
    
    Args:
        app: FastAPI application instance
        include_details: Whether to include error details in responses
    """
    
    @app.exception_handler(GlamBaseError)
    async def glam_error_handler(request: Request, exc: GlamBaseError):
        """Handle our custom domain/infrastructure errors."""
        request_id = getattr(request.state, "request_id", None)
        correlation_id = getattr(request.state, "correlation_id", None)
        
        error_response, status_code = exception_to_error_response(
            exc,
            request_id=request_id,
            correlation_id=correlation_id,
            include_details=include_details,
            log_traceback=False  # Don't log expected errors
        )
        
        return JSONResponse(
            content=error_response.dict(),
            status_code=status_code
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        request_id = getattr(request.state, "request_id", None)
        correlation_id = getattr(request.state, "correlation_id", None)
        
        # Convert Pydantic errors to our format
        validation_errors = []
        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            validation_errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })
        
        # Create a ValidationError with details
        validation_exc = ValidationError(
            "Request validation failed",
            details={"validation_errors": validation_errors}
        )
        
        error_response, status_code = exception_to_error_response(
            validation_exc,
            request_id=request_id,
            correlation_id=correlation_id,
            include_details=include_details
        )
        
        return JSONResponse(
            content=error_response.dict(),
            status_code=status_code
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle FastAPI HTTP exceptions."""
        request_id = getattr(request.state, "request_id", None)
        correlation_id = getattr(request.state, "correlation_id", None)
        
        # Map common HTTP exceptions to our error types
        if exc.status_code == 401:
            from .base import UnauthorizedError
            domain_exc = UnauthorizedError(exc.detail)
        elif exc.status_code == 403:
            from .base import ForbiddenError
            domain_exc = ForbiddenError(exc.detail)
        elif exc.status_code == 404:
            from .base import NotFoundError
            domain_exc = NotFoundError(exc.detail)
        else:
            # Generic error
            domain_exc = GlamBaseError(
                exc.detail,
                code="HTTP_ERROR",
                status=exc.status_code
            )
        
        error_response, status_code = exception_to_error_response(
            domain_exc,
            request_id=request_id,
            correlation_id=correlation_id,
            include_details=include_details
        )
        
        return JSONResponse(
            content=error_response.dict(),
            status_code=status_code
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors."""
        request_id = getattr(request.state, "request_id", None)
        correlation_id = getattr(request.state, "correlation_id", None)
        
        error_response, status_code = exception_to_error_response(
            exc,
            request_id=request_id,
            correlation_id=correlation_id,
            include_details=include_details,
            log_traceback=True
        )
        
        return JSONResponse(
            content=error_response.dict(),
            status_code=status_code
        )


@asynccontextmanager
async def get_request_id(request: Request):
    """
    Context manager to access the current request's ID.
    
    Usage:
        async with get_request_id(request) as request_id:
            # Use request_id in your code
    """
    request_id = getattr(request.state, "request_id", None)
    if not request_id:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = request_id
    
    yield request_id
