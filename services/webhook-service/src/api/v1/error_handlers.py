# services/webhook-service/src/api/v1/error_handlers.py
"""Error handlers for webhook API endpoints."""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_413_REQUEST_ENTITY_TOO_LARGE, HTTP_422_UNPROCESSABLE_ENTITY

from ...errors import (
    InvalidSignatureError,
    WebhookValidationError,
    PayloadTooLargeError,
    DuplicateWebhookError,
    PlatformNotSupportedError
)


async def invalid_signature_handler(request: Request, exc: InvalidSignatureError) -> JSONResponse:
    """Handle invalid signature errors."""
    return JSONResponse(
        status_code=HTTP_401_UNAUTHORIZED,
        content={
            "error": "invalid_signature",
            "message": exc.message,
            "code": exc.error_code
        }
    )


async def webhook_validation_handler(request: Request, exc: WebhookValidationError) -> JSONResponse:
    """Handle webhook validation errors."""
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": exc.message,
            "code": exc.error_code
        }
    )


async def payload_too_large_handler(request: Request, exc: PayloadTooLargeError) -> JSONResponse:
    """Handle payload too large errors."""
    return JSONResponse(
        status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        content={
            "error": "payload_too_large",
            "message": exc.message,
            "code": exc.error_code
        }
    )


async def duplicate_webhook_handler(request: Request, exc: DuplicateWebhookError) -> JSONResponse:
    """Handle duplicate webhook errors."""
    return JSONResponse(
        status_code=200,  # Return 200 for duplicates to prevent retries
        content={
            "success": True,
            "message": exc.message,
            "code": exc.error_code
        }
    )


async def platform_not_supported_handler(request: Request, exc: PlatformNotSupportedError) -> JSONResponse:
    """Handle platform not supported errors."""
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "platform_not_supported",
            "message": exc.message,
            "code": exc.error_code
        }
    )
