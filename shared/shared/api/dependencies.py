"""
FastAPI dependencies for standardized API behavior.
Clean, generic, production-ready dependencies.
"""

from typing import Annotated, Optional, TYPE_CHECKING
import jwt
import os
import re
from fastapi import Query, Request, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .correlation import get_correlation_id

if TYPE_CHECKING:
    from shared.utils.logger import ServiceLogger



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


PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]

# =========================
# Logger Dependency  
# =========================

def get_logger(request: Request) -> "ServiceLogger":
    """Get the service logger from app state."""
    return request.app.state.logger


LoggerDep = Annotated["ServiceLogger", Depends(get_logger)]


# =========================
# Request Context
# =========================

def get_request_id(request: Request) -> str:
    if not hasattr(request.state, "request_id"):
        raise RuntimeError("Request ID not found. Ensure APIMiddleware is properly configured.")
    return request.state.request_id


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_content_type(request: Request) -> Optional[str]:
    return request.headers.get("Content-Type")


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


# Type annotations
ClientIpDep = Annotated[str, Depends(get_client_ip)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
ContentTypeDep = Annotated[Optional[str], Depends(get_content_type)]
CorrelationIdDep = Annotated[str, Depends(get_correlation_id)]
RequestContextDep = Annotated[RequestContext, Depends(get_request_context)]


# =========================
# Platform & Domain Context
# =========================

SUPPORTED_PLATFORMS = {
    "shopify", 
    "bigcommerce", 
    "woocommerce", 
    "magento", 
    "squarespace",
    "custom"
}


class PlatformContext(BaseModel):
    """Generic platform and domain information."""
    platform: str
    domain: str
    
    @property
    def is_shopify(self) -> bool:
        return self.platform == "shopify"
    
    @property
    def is_custom_domain(self) -> bool:
        """Check if domain appears to be a custom domain vs platform default."""
        if self.platform == "shopify":
            return not self.domain.endswith(".myshopify.com")
        elif self.platform == "bigcommerce":
            return not self.domain.endswith(".mybigcommerce.com")
        return True


def _validate_platform(platform: str) -> str:
    """Validate and normalize platform name."""
    platform_norm = platform.strip().lower()
    
    if platform_norm not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "UNSUPPORTED_PLATFORM",
                "message": f"Platform '{platform}' is not supported",
                "details": {
                    "received": platform,
                    "supported_platforms": sorted(SUPPORTED_PLATFORMS)
                }
            }
        )
    
    return platform_norm


def _validate_domain(domain: str) -> str:
    """Generic domain validation - works for any platform."""
    domain_norm = domain.strip().lower()
    
    # Basic domain format validation
    domain_pattern = r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$"
    
    if not re.match(domain_pattern, domain_norm):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_DOMAIN_FORMAT",
                "message": f"Invalid domain format: '{domain}'",
                "details": {
                    "received": domain,
                    "expected_format": "Valid domain name (e.g., shop.example.com, my-store.myshopify.com)"
                }
            }
        )
    
    if len(domain_norm) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain name too long (max 255 characters)"
        )
    
    return domain_norm


def require_platform_context(request: Request) -> PlatformContext:
    """
    Extract and validate shop platform and domain from headers.
    
    Expected headers:
    - X-Shop-Platform: The e-commerce platform (shopify, bigcommerce, etc.)
    - X-Shop-Domain: The shop's domain (can be platform domain or custom)
    """
    
    platform = request.headers.get("X-Shop-Platform")
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MISSING_PLATFORM_HEADER",
                "message": "Missing required shop platform header",
                "details": {
                    "expected_header": "X-Shop-Platform",
                    "supported_platforms": sorted(SUPPORTED_PLATFORMS)
                }
            }
        )
    
    domain = request.headers.get("X-Shop-Domain")
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MISSING_DOMAIN_HEADER", 
                "message": "Missing required shop domain header",
                "details": {
                    "expected_header": "X-Shop-Domain"
                }
            }
        )
    
    platform_norm = _validate_platform(platform)
    domain_norm = _validate_domain(domain)
    
    return PlatformContext(platform=platform_norm, domain=domain_norm)


def require_shop_platform(request: Request) -> str:
    """Extract just the platform."""
    return require_platform_context(request).platform


def require_shop_domain(request: Request) -> str:
    """Extract just the domain."""
    return require_platform_context(request).domain


# Type annotations
PlatformContextDep = Annotated[PlatformContext, Depends(require_platform_context)]
ShopPlatformDep = Annotated[str, Depends(require_shop_platform)]
ShopDomainDep = Annotated[str, Depends(require_shop_domain)]


# =========================
# Authentication
# =========================

class ClientAuthContext(BaseModel):
    """Client authentication result with shop context."""
    shop: str
    scope: str
    token: str
    
    @property
    def audience(self) -> str:
        return "client"


class InternalAuthContext(BaseModel):
    """Internal service-to-service authentication result."""
    service: str  # Identifying which service made the request
    token: str
    
    @property
    def audience(self) -> str:
        return "internal"


def _get_bearer_token(request: Request) -> str:
    """Extract bearer token from Authorization header."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing bearer token"
        )
    return auth.split(" ", 1)[1].strip()


def require_client_auth(request: Request) -> ClientAuthContext:
    """
    Client authentication using JWTs.
    For requests from client applications with shop context.
    """
    token = _get_bearer_token(request)
    secret = os.getenv("CLIENT_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("CLIENT_JWT_SECRET not configured")
    
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Invalid JWT: {str(e)}"
        )
    
    return ClientAuthContext(
        shop=payload.get("sub", ""),
        scope=payload.get("scope", ""),
        token=token
    )


def require_internal_auth(request: Request) -> InternalAuthContext:
    """
    Internal service-to-service authentication.
    Uses static API keys for simplicity and performance.
    """
    token = _get_bearer_token(request)
    raw = os.getenv("INTERNAL_API_KEYS", "")
    if not raw:
        raise RuntimeError("INTERNAL_API_KEYS not configured")
    
    # Format: "service1:key1,service2:key2" or just "key1,key2"
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid bearer token"
        )
    
    return InternalAuthContext(
        service=allowed[token],
        token=token
    )


# Type annotations
ClientAuthDep = Annotated[ClientAuthContext, Depends(require_client_auth)]
InternalAuthDep = Annotated[InternalAuthContext, Depends(require_internal_auth)]


# =========================
# Webhook Headers
# =========================

class WebhookHeaders(BaseModel):
    """Generic webhook headers that work across platforms."""
    platform: str
    topic: str
    shop_domain: str
    webhook_id: Optional[str] = None
    
    @property
    def is_shopify_webhook(self) -> bool:
        return self.platform == "shopify"


def get_webhook_headers(request: Request) -> WebhookHeaders:
    """
    Extract webhook headers that work across different platforms.
    
    Expected headers:
    - X-Webhook-Platform: The platform sending the webhook
    - X-Webhook-Topic: The webhook event type
    - X-Shop-Domain: The shop domain 
    - X-Webhook-Id: Optional webhook identifier
    """
    headers = request.headers
    
    platform = headers.get("X-Webhook-Platform")
    topic = headers.get("X-Webhook-Topic")  
    shop_domain = headers.get("X-Shop-Domain")
    webhook_id = headers.get("X-Webhook-Id")
    
    # Check for missing required headers
    missing = []
    if not platform:
        missing.append("X-Webhook-Platform")
    if not topic:
        missing.append("X-Webhook-Topic")
    if not shop_domain:
        missing.append("X-Shop-Domain")
    
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MISSING_WEBHOOK_HEADERS",
                "message": f"Missing required webhook headers: {', '.join(missing)}",
                "details": {"missing_headers": missing}
            }
        )
    
    # Validate platform and domain
    platform_norm = _validate_platform(platform) # type: ignore
    domain_norm = _validate_domain(shop_domain) # type: ignore
    
    # Basic validation for header sizes
    if len(topic) > 256: # type: ignore
        raise HTTPException(status_code=400, detail="X-Webhook-Topic too long")
    if webhook_id and len(webhook_id) > 256:
        raise HTTPException(status_code=400, detail="X-Webhook-Id too long")
    
    return WebhookHeaders(
        platform=platform_norm,
        topic=topic, # type: ignore
        shop_domain=domain_norm,
        webhook_id=webhook_id
    )


WebhookHeadersDep = Annotated[WebhookHeaders, Depends(get_webhook_headers)]