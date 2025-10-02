# shared/api/handlers.py

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .responses import error_response


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        correlation_id = getattr(request.state, "correlation_id", None)
        return JSONResponse(
            content=error_response(
                code=(exc.detail.get("code") if isinstance(exc.detail, dict) else f"HTTP_{exc.status_code}"),
                message=(exc.detail.get("message") if isinstance(exc.detail, dict) else str(exc.detail)),
                details=(exc.detail.get("details") if isinstance(exc.detail, dict) else None),
                correlation_id=correlation_id,
            ).model_dump(mode="json", exclude_none=True),
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        correlation_id = getattr(request.state, "correlation_id", None)
        validation_errors = [
            {
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=error_response(
                code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"validation_errors": validation_errors},
                correlation_id=correlation_id,
            ).model_dump(mode="json", exclude_none=True),
        )
