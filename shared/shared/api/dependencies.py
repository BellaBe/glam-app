"""
FastAPI dependencies for standardized API behavior.
Clean, generic, production-ready dependencies.
"""

import os
from typing import TYPE_CHECKING, Annotated

import jwt
from fastapi import Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from shared.utils.logger import ServiceLogger


def _lc(s: str | None) -> str:
    return (s or "").strip().lower()


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


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_platform(request: Request) -> str:
    return request.headers.get("X-Shop-Platform")


def get_domain(request: Request) -> str:
    return request.headers.get("X-Shop-Domain")


def get_content_type(request: Request) -> str:
    return request.headers.get("Content-Type")


class RequestContext(BaseModel):
    correlation_id: str  # set by middleware; enforced to exist
    method: str
    path: str  # request.url.path (info only)
    base_path: str  # SAFE: scope.root_path + scope.path
    query_params: dict[str, str]  # current query params flattened
    content_type: str | None
    ip_client: str
    platform: str | None
    domain: str | None

    @property
    def is_shopify(self) -> bool:
        return _lc(self.platform) == "shopify"

    @classmethod
    def from_request(cls, request: Request) -> "RequestContext":
        # correlation id was validated by middleware; read from state
        cid = request.state.correlation_id
        scope_path = f"{request.scope.get('root_path', '')}{request.scope['path']}"
        return cls(
            correlation_id=cid,
            method=request.method,
            path=str(request.url.path),
            base_path=scope_path,
            query_params=dict(request.query_params),  # flattened is fine for our filters
            content_type=get_content_type(request),
            ip_client=get_client_ip(request),
            platform=get_platform(request),
            domain=get_domain(request),
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


REQUIRED_CLIENT_SCOPE = os.getenv("REQUIRED_CLIENT_SCOPE", "bff:api:access")
REQUIRED_PLATFORM = "shopify"


def require_client_auth(request: Request, ctx: RequestContextDep) -> ClientAuthContext:
    token = _get_bearer_token(request)
    secret = os.getenv("CLIENT_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("CLIENT_JWT_SECRET not configured")

    try:
        payload = jwt.decode(token, secret, algorithms=[os.getenv("JWT_ALGORITHM", "HS256")])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid JWT: {e!s}") from e

    jwt_shop = _lc(payload.get("sub", ""))
    jwt_scope = _lc(payload.get("scope", ""))

    # Critical MVP checks live HERE (no extra validator):
    # 1) Platform must be shopify
    if not ctx.is_shopify:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PLATFORM", "message": f"Only '{REQUIRED_PLATFORM}' platform is supported"},
        )

    # 2) Header domain must exist and match JWT shop
    if not ctx.domain or jwt_shop != ctx.domain:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "DOMAIN_MISMATCH", "message": "JWT shop does not match X-Shop-Domain"},
        )

    # 3) Scope must match required scope
    if jwt_scope != _lc(REQUIRED_CLIENT_SCOPE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "INVALID_SCOPE", "message": f"Required scope '{REQUIRED_CLIENT_SCOPE}'"},
        )

    return ClientAuthContext(shop=jwt_shop, scope=jwt_scope, token=token)


ClientAuthDep = Annotated[ClientAuthContext, Depends(require_client_auth)]


def require_internal_auth(request: Request, ctx: RequestContextDep) -> InternalAuthContext:
    token = _get_bearer_token(request)

    secret = os.getenv("INTERNAL_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("INTERNAL_JWT_SECRET not configured")

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[os.getenv("JWT_ALGORITHM", "HS256")],
            options={"require": ["sub"]},  # minimal: require service identity
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid internal JWT: {e!s}",
        ) from e

    service = str(payload.get("sub", "")).strip().lower()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal JWT: missing subject",
        )

    return InternalAuthContext(service=service, token=token)


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
