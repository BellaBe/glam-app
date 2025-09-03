"""
FastAPI dependencies for standardized API behavior.
Clean, generic, production-ready dependencies.
"""

import os
import uuid
from typing import TYPE_CHECKING, Annotated

import jwt
from fastapi import Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from shared.utils.logger import ServiceLogger


# Pagination
class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=1000)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page"),
) -> PaginationParams:
    return PaginationParams(page=page, limit=limit)


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]


# Logger
def get_logger(request: Request) -> "ServiceLogger":
    return request.app.state.logger


LoggerDep = Annotated["ServiceLogger", Depends(get_logger)]


# Request Context Utilities
def get_correlation_id(request: Request) -> str:
    return request.headers.get("X-Correlation-ID", f"corr_{uuid.uuid4().hex[:12]}")


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_content_type(request: Request) -> str | None:
    return request.headers.get("Content-Type")


class RequestContext(BaseModel):
    """Essential request context for logging/auditing."""

    correlation_id: str
    method: str
    path: str
    content_type: str | None = None
    ip_client: str | None = None

    @classmethod
    def from_request(cls, request: Request) -> "RequestContext":
        return cls(
            correlation_id=get_correlation_id(request),
            method=request.method,
            path=str(request.url.path),
            ip_client=get_client_ip(request),
            content_type=get_content_type(request),
        )


def get_request_context(request: Request) -> RequestContext:
    return RequestContext.from_request(request)


RequestContextDep = Annotated[RequestContext, Depends(get_request_context)]


# Platform headers
SUPPORTED_PLATFORMS = {"shopify", "bigcommerce", "woocommerce", "magento", "squarespace", "custom"}


# Authentication
class ClientAuthContext(BaseModel):
    shop: str
    scope: str
    token: str

    @property
    def audience(self) -> str:
        return "client"


class InternalAuthContext(BaseModel):
    service: str
    token: str

    @property
    def audience(self) -> str:
        return "internal"


def _get_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return auth.split(" ", 1)[1].strip()


def require_client_auth(request: Request) -> ClientAuthContext:
    token = _get_bearer_token(request)
    secret = os.getenv("CLIENT_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("CLIENT_JWT_SECRET not configured")

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid JWT: {e!s}") from e

    return ClientAuthContext(
        shop=payload.get("sub", ""),
        scope=payload.get("scope", ""),
        token=token,
    )


def require_internal_auth(request: Request) -> InternalAuthContext:
    token = _get_bearer_token(request)
    raw = os.getenv("INTERNAL_JWT_SECRET", "")
    if not raw:
        raise RuntimeError("INTERNAL_JWT_SECRET not configured")

    allowed = {}
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" in entry:
            service, key = entry.split(":", 1)
            allowed[key.strip()] = service.strip()
        else:
            allowed[entry] = "unknown"

    if token not in allowed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

    return InternalAuthContext(service=allowed[token], token=token)


ClientAuthDep = Annotated[ClientAuthContext, Depends(require_client_auth)]
InternalAuthDep = Annotated[InternalAuthContext, Depends(require_internal_auth)]


# Webhooks
class WebhookHeaders(BaseModel):
    topic: str
    webhook_id: str | None = None

    @property
    def event_type(self) -> str:
        return self.topic.replace("/", ".").replace("_", ".")


def get_webhook_headers(request: Request) -> WebhookHeaders:
    topic = request.headers.get("X-Webhook-Topic")
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MISSING_WEBHOOK_TOPIC",
                "message": "Missing required webhook topic header",
                "details": {"expected_header": "X-Webhook-Topic"},
            },
        )

    if len(topic) > 256:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Webhook-Topic too long")

    webhook_id = request.headers.get("X-Webhook-Id")
    if webhook_id and len(webhook_id) > 256:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Webhook-Id too long")

    return WebhookHeaders(topic=topic, webhook_id=webhook_id)


WebhookHeadersDep = Annotated[WebhookHeaders, Depends(get_webhook_headers)]
