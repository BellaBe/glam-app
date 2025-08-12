# File: shared/api/dependencies.py

"""
FastAPI dependencies for standardized API behavior.

Simplified to focus on commonly used dependencies.
"""

from typing import Annotated, Optional, Iterable
import jwt
from fastapi import Query, Request, Depends, HTTPException, status
from pydantic import BaseModel, Field
import os, re

from .correlation import get_correlation_id


# =========================
# Pagination
# =========================

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


# =========================
# Request IDs / IP
# =========================

def get_request_id(request: Request) -> str:
    if not hasattr(request.state, "request_id"):
        raise RuntimeError(
            "Request ID not found. Ensure APIMiddleware is properly configured."
        )
    return request.state.request_id


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_content_type(request: Request) -> Optional[str]:
    """
    Get the content type from the request headers.
    Returns None if not set.
    """
    return request.headers.get("Content-Type")


ClientIpDep = Annotated[str, Depends(get_client_ip)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
ContentTypeDep = Annotated[Optional[str], Depends(get_content_type)]


# =========================
# Correlation / Context
# =========================

CorrelationIdDep = Annotated[str, Depends(get_correlation_id)]  # Re-export

class RequestContext(BaseModel):
    """Essential request context for logging/auditing."""
    request_id: str
    correlation_id: str
    method: str
    path: str
    content_type: Optional[str] = None
    ip_client: Optional[str] = None
    

    @classmethod
    def from_request(cls, request: Request) -> "RequestContext":
        return cls(
            request_id=get_request_id(request),
            correlation_id=get_correlation_id(request),
            method=request.method,
            path=str(request.url.path),
            ip_client=get_client_ip(request),
            content_type=get_content_type(request),
        )


def get_request_context(request: Request) -> RequestContext:
    return RequestContext.from_request(request)


RequestContextDep = Annotated[RequestContext, Depends(get_request_context)]


# =========================
# Auth (Bearer) deps
# =========================

class AuthContext(BaseModel):
    """Authentication result."""
    audience: str  # "fe" | "internal"
    token: str


def _bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return auth.split(" ", 1)[1].strip()


def _require_exact_token(token: str, expected: str, audience: str) -> AuthContext:
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
    return AuthContext(audience=audience, token=token)


def _require_any_token(token: str, allowed: Iterable[str], audience: str) -> AuthContext:
    if token not in allowed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")
    return AuthContext(audience=audience, token=token)


def require_backend_auth(request: Request) -> AuthContext:
    """
    Public FE → service auth (BACKEND_API_KEY).
    """
    token = _bearer_token(request)
    expected = os.getenv("BACKEND_API_KEY", "")
    if not expected:
        raise RuntimeError("BACKEND_API_KEY not configured")
    return _require_exact_token(token, expected, audience="fe")


def require_internal_auth(request: Request) -> AuthContext:
    """
    Service-to-service auth. Comma-separated INTERNAL_API_KEYS is supported.
    """
    token = _bearer_token(request)
    raw = os.getenv("INTERNAL_API_KEYS", "")
    if not raw:
        raise RuntimeError("INTERNAL_API_KEYS not configured")
    allowed = {k.strip() for k in raw.split(",") if k.strip()}
    return _require_any_token(token, allowed, audience="internal")


AuthDep = Annotated[AuthContext, Depends(require_backend_auth)]
InternalAuthDep = Annotated[AuthContext, Depends(require_internal_auth)]


# =========================
# Shop domain dep
# =========================

_MYSHOPIFY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.myshopify\.com$")


def _normalize_myshopify(value: str) -> str:
    v = (value or "").strip().lower()
    if not _MYSHOPIFY_RE.match(v):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Shop-Domain (must be canonical myshopify domain)",
        )
    return v


def require_shop_domain(request: Request) -> str:
    """
    Extract and validate canonical myshopify domain from 'X-Shop-Domain' header.
    """
    hdr = request.headers.get("X-Shop-Domain")
    if not hdr:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Shop-Domain header",
        )
    return _normalize_myshopify(hdr)


ShopDomainDep = Annotated[str, Depends(require_shop_domain)]


# =========================
# Pagination alias
# =========================

PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]


# =========================
# JWT-based internal auth
# =========================

class JwtAuthContext(BaseModel):
    """JWT Authentication result."""
    audience: str  # "internal" or "fe"
    shop: str
    scope: str
    token: str

def require_internal_jwt(request: Request) -> JwtAuthContext:
    """
    Service-to-service auth with short-lived JWT.
    Uses INTERNAL_JWT_SECRET to verify.
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = auth.split(" ", 1)[1].strip()
    secret = os.getenv("INTERNAL_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("INTERNAL_JWT_SECRET not configured")
    
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid JWT: {str(e)}")
    
    return JwtAuthContext(
        audience="internal",
        shop=payload.get("sub", ""),
        scope=payload.get("scope", ""),
        token=token
    )

InternalJwtDep = Annotated[JwtAuthContext, Depends(require_internal_jwt)]


# =========================
# Shopify webhook headers
# =========================

class ShopifyWebhookHeaders(BaseModel):
    """
    Canonicalized Shopify webhook headers extracted from the request.
    """
    topic_raw: str
    shop_domain: str
    webhook_id: Optional[str] = None

def get_shopify_webhook_headers(
    request: Request,
) -> ShopifyWebhookHeaders:
    """
    Extracts and validates Shopify webhook headers from a BFF-relayed request.
    Assumes the BFF already verified origin (no HMAC here).
    """
    # FastAPI's Header(...) could be used, but pulling from request.headers keeps this dep reusable in middleware too.
    headers = request.headers


    topic = headers.get("X-Shopify-Topic")
    shop = headers.get("X-Shopify-Shop-Domain")
    webhook_id = headers.get("X-Shopify-Webhook-Id")

    missing = [name for name, val in [
        ("X-Shopify-Topic", topic),
        ("X-Shopify-Shop-Domain", shop),
        ("X-Shopify-Webhook-Id", webhook_id),
    ] if not val]
    
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required headers: {', '.join(missing)}"
        )

    # Normalize and validate domain
    try:
        shop_norm = _normalize_myshopify(shop) #type: ignore
    except HTTPException: 
        # Re-raise with the same error for consistency
        raise

    # (Optional) lightweight sanity checks to avoid absurd header sizes
    if len(webhook_id) > 256: #type: ignore
        raise HTTPException(status_code=400, detail="X-Shopify-Webhook-Id too long")
    if len(topic) > 256: #type: ignore
        raise HTTPException(status_code=400, detail="X-Shopify-Topic too long")

    return ShopifyWebhookHeaders(
        webhook_id=webhook_id, #type: ignore
        topic_raw=topic, #type: ignore
        shop_domain=shop_norm,
    )

ShopifyHeadersDep = Annotated[ShopifyWebhookHeaders, Depends(get_shopify_webhook_headers)]