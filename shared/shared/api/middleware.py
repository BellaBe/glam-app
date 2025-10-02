# shared/api/middleware.py
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from shared.utils.exceptions import GlamBaseError
from shared.utils.logger import ServiceLogger

from .responses import error_response


def setup_middleware(app: FastAPI, *, service_name: str):
    """
    Registers a single function-style HTTP middleware that:
      - enforces X-Correlation-ID (400 if missing)
      - sets request.state.correlation_id
      - sets logger context
      - logs success/failure with timing
      - guarantees response headers (X-Correlation-ID, X-Service-Name)
      - formats ALL errors into ApiResponse via _handle_exception
    """

    async def _handle_exception(exc: Exception, correlation_id: str | None):
        if isinstance(exc, GlamBaseError):
            return exc.status, error_response(
                code=exc.code, message=exc.message, details=exc.details, correlation_id=correlation_id
            )

        if isinstance(exc, RequestValidationError):
            validation_errors = [
                {"field": ".".join(map(str, e["loc"])), "message": e["msg"], "type": e["type"]} for e in exc.errors()
            ]
            return 422, error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"validation_errors": validation_errors},
                correlation_id=correlation_id,
            )

        if isinstance(exc, FastAPIHTTPException):
            if isinstance(exc.detail, dict):
                return exc.status_code, error_response(
                    code=exc.detail.get("code", f"HTTP_{exc.status_code}"),
                    message=exc.detail.get("message", str(exc.detail)),
                    details=exc.detail.get("details"),
                    correlation_id=correlation_id,
                )
            return exc.status_code, error_response(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                details=None,
                correlation_id=correlation_id,
            )

        return 500, error_response(
            code="INTERNAL_ERROR",
            message=f"An unexpected error occurred: {exc!s}",
            details={"type": type(exc).__name__},
            correlation_id=correlation_id,
        )

    @app.middleware("http")
    async def api_middleware(request: Request, call_next):
        logger: ServiceLogger = request.app.state.logger
        start = time.perf_counter()

        try:
            # 1) enforce correlation id
            correlation_id = request.headers.get("X-Correlation-ID")
            if not correlation_id:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "MISSING_CORRELATION_ID",
                        "message": "X-Correlation-ID header is required",
                        "details": {"expected_header": "X-Correlation-ID"},
                    },
                )

            # 2) stash on state for everyone else
            request.state.correlation_id = correlation_id

            # 3) set logging context
            logger.set_request_context(
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                service=service_name,
            )

            # 4) proceed
            response = await call_next(request)

            # 5) success logging
            logger.info(
                "Request completed",
                extra={"status": response.status_code, "duration_ms": round((time.perf_counter() - start) * 1000, 2)},
            )

        except Exception as exc:
            # uniform error response
            cid = getattr(request.state, "correlation_id", request.headers.get("X-Correlation-ID"))
            status_code, payload = await _handle_exception(exc, cid)

            logger.exception(
                "Request failed",
                extra={
                    "status": status_code,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                    "error_code": payload.error.code if payload.error else "UNKNOWN",
                    "error_type": type(exc).__name__,
                },
            )

            response = JSONResponse(content=payload.model_dump(mode="json", exclude_none=True), status_code=status_code)

        finally:
            logger.clear_request_context()

        # 6) always set headers (guard cid)
        cid = getattr(request.state, "correlation_id", request.headers.get("X-Correlation-ID"))
        if cid:
            response.headers["X-Correlation-ID"] = cid
        response.headers["X-Service-Name"] = service_name
        return response
