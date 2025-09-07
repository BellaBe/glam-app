# shared/api/middleware.py

"""API middleware."""

import time
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from shared.utils.exceptions import GlamBaseError
from shared.utils.logger import ServiceLogger

from .responses import error_response


class APIMiddleware(BaseHTTPMiddleware):
    """Unified middleware for request/response handling."""

    def __init__(self, app: FastAPI, *, service_name: str = "glam-service"):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID")
        logger: ServiceLogger = request.app.state.logger
        
        # Set logging context at request start
        logger.set_request_context(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            service=self.service_name
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Request completed",
                extra={
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
        except Exception as exc:
            status_code, error_resp = self._handle_exception(exc, correlation_id)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "Request failed",
                extra={
                    "status": status_code,
                    "duration_ms": duration_ms,
                    "error_code": error_resp.error.code if error_resp.error else "UNKNOWN",
                    "error_type": type(exc).__name__,
                }
            )

            response = JSONResponse(
                content=error_resp.model_dump(mode="json", exclude_none=True),
                status_code=status_code,
            )
        
        # Clear logging context after request completion
        finally:
            logger.clear_request_context()

        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Service-Name"] = self.service_name
        return response

    def _handle_exception(self, exc: Exception, correlation_id: str):
        """Convert exception to standardized error response."""

        if isinstance(exc, GlamBaseError):
            return exc.status, error_response(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                correlation_id=correlation_id,
            )

        elif isinstance(exc, RequestValidationError):
            validation_errors = [
                {
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ]
            return 422, error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"validation_errors": validation_errors},
                correlation_id=correlation_id,
            )

        elif isinstance(exc, HTTPException):
            if isinstance(exc.detail, dict):
                return exc.status_code, error_response(
                    code=exc.detail.get("code", f"HTTP_{exc.status_code}"),
                    message=exc.detail.get("message", str(exc.detail)),
                    details=exc.detail.get("details", exc.detail),
                    correlation_id=correlation_id,
                )
            return exc.status_code, error_response(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                details=None,
                correlation_id=correlation_id,
            )

        # Unknown/unhandled exception
        return 500, error_response(
            code="INTERNAL_ERROR",
            message=f"An unexpected error occurred: {exc!s}",
            details={"type": type(exc).__name__},
            correlation_id=correlation_id,
        )


def setup_middleware(app: FastAPI, *, service_name: str):
    """Add core middleware to FastAPI app."""
    app.add_middleware(APIMiddleware, service_name=service_name)
