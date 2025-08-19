# shared/api/debug.py
# ruff: noqa: T201
"""Debug utilities for FastAPI applications."""

import json
import logging
from collections.abc import Callable

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class EarlyDebugMiddleware(BaseHTTPMiddleware):
    """Debug middleware that runs before any dependencies or validation."""

    async def dispatch(self, request: Request, call_next: Callable):
        print("\n" + "=" * 60)
        print("🔍 EARLY DEBUG - REQUEST RECEIVED")
        print("=" * 60)

        # Log all request details
        print(f"🌐 URL: {request.url}")
        print(f"📍 Path: {request.url.path}")
        print(f"🔧 Method: {request.method}")
        print(f"❓ Query Params: {dict(request.query_params)}")

        # Log all headers
        print("📋 Headers:")
        for name, value in request.headers.items():
            # Mask authorization for security
            if name.lower() == "authorization":
                value = f"Bearer {value[7:17]}..." if value.startswith("Bearer ") else "***"
            print(f"   {name}: {value}")

        # Log body for POST/PUT/PATCH WITHOUT consuming it
        body_logged = False
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body once and store it
                body = await request.body()
                if body:
                    try:
                        body_json = json.loads(body)
                        print("📦 Body (JSON):")
                        print(json.dumps(body_json, indent=2))
                        body_logged = True
                    except json.JSONDecodeError:
                        body_str = body.decode("utf-8", errors="ignore")
                        print(f"📦 Body (Raw): {body_str[:200]}{'...' if len(body_str) > 200 else ''}")
                        body_logged = True
                else:
                    print("📦 Body: (empty)")
                    body_logged = True

            except Exception as e:
                print(f"📦 Body: (error reading: {e})")

        if not body_logged:
            print("📦 Body: (no body for GET request)")

        print("⏳ Calling next middleware/handler...")
        print("=" * 60)

        try:
            response = await call_next(request)

            print("\n" + "=" * 60)
            print("✅ EARLY DEBUG - RESPONSE READY")
            print("=" * 60)
            print(f"📤 Status: {response.status_code}")
            print(f"📤 Headers: {dict(response.headers)}")
            print("=" * 60 + "\n")

            return response

        except Exception as e:
            print("\n" + "=" * 60)
            print("❌ EARLY DEBUG - EXCEPTION CAUGHT")
            print("=" * 60)
            print(f"💥 Exception Type: {type(e).__name__}")
            print(f"💥 Exception Message: {e!s}")
            print(f"💥 Exception Details: {getattr(e, 'detail', 'No details')}")
            if hasattr(e, "status_code"):
                print(f"💥 Status Code: {e.status_code}")
            print("=" * 60 + "\n")
            raise  # Re-raise to let other handlers deal with it


def setup_debug_middleware(app: FastAPI):
    """Add debug middleware as the first middleware."""
    app.add_middleware(EarlyDebugMiddleware)


def setup_debug_handlers(app: FastAPI):
    """Add debug exception handlers to catch errors before middleware."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Debug validation errors in detail."""

        print("=" * 50)
        print("🚨 VALIDATION ERROR CAUGHT!")
        print("=" * 50)

        # Log request details
        print(f"📥 Request URL: {request.url}")
        print(f"📥 Request Method: {request.method}")
        print("📥 Request Headers:")
        for name, value in request.headers.items():
            print(f"   {name}: {value}")

        # Log request body if available
        try:
            if request.method in ["POST", "PUT", "PATCH"]:
                # Try to get body (might be consumed already)
                body = await request.body()
                if body:
                    try:
                        body_json = json.loads(body)
                        print(f"📥 Request Body (JSON): {json.dumps(body_json, indent=2)}")
                    except Exception:
                        print(f"📥 Request Body (Raw): {body.decode('utf-8', errors='ignore')[:500]}...")
                else:
                    print("📥 Request Body: (empty)")
        except Exception as e:
            print(f"📥 Request Body: (error reading: {e})")

        # Log validation errors in detail
        print(f"❌ Validation Errors ({len(exc.errors())} total):")
        for i, error in enumerate(exc.errors()):
            print(f"   {i + 1}. Field: {error.get('loc', 'unknown')}")
            print(f"      Type: {error.get('type', 'unknown')}")
            print(f"      Message: {error.get('msg', 'unknown')}")
            print(f"      Input: {error.get('input', 'not provided')}")
            print()

        print("=" * 50)

        # Return structured error response
        validation_errors = []
        for error in exc.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            validation_errors.append(
                {"field": field_path, "message": error["msg"], "type": error["type"], "input": error.get("input")}
            )

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"validation_errors": validation_errors, "total_errors": len(validation_errors)},
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Debug HTTP exceptions."""

        print("=" * 50)
        print(f"🚨 HTTP EXCEPTION: {exc.status_code}")
        print("=" * 50)
        print(f"📥 Request URL: {request.url}")
        print(f"📥 Request Method: {request.method}")
        print(f"❌ Exception Detail: {exc.detail}")
        print(f"❌ Exception Type: {type(exc.detail)}")
        print("=" * 50)

        # Let your middleware handle this
        raise exc

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Catch any other exceptions."""

        print("=" * 50)
        print(f"🚨 GENERAL EXCEPTION: {type(exc).__name__}")
        print("=" * 50)
        print(f"📥 Request URL: {request.url}")
        print(f"📥 Request Method: {request.method}")
        print(f"❌ Exception: {exc}")
        print("=" * 50)

        # Let your middleware handle this
        raise exc
