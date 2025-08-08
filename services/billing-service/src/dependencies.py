from typing import Annotated, Optional
from fastapi import Depends, Request, HTTPException, Header
from prisma import Prisma
import redis.asyncio as redis
from shared.api.dependencies import RequestIdDep, PaginationDep, CorrelationIdDep, RequestContextDep
from shared.messaging.jetstream_client import JetStreamClient
from .lifecycle import ServiceLifecycle
from .config import ServiceConfig
from .services.billing_service import BillingService
from .services.webhook_service import WebhookProcessingService
from .events.publishers import BillingEventPublisher

# Re-export shared dependencies
__all__ = [
    "PrismaDep",
    "CorrelationIdDep", 
    "PaginationDep",
    "RequestIdDep",
    "RequestContextDep",
    "LifecycleDep",
    "ConfigDep",
    "BillingServiceDep",
    "WebhookServiceDep",
    "PublisherDep",
    "RedisDep",
    "ShopDomainDep",
    "IdempotencyKeyDep",
    "BearerTokenDep",
    "AdminAuthDep",
    "FrontendAuthDep"
]

# Core dependencies
def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle

def get_config(request: Request) -> ServiceConfig:
    """Get service config from app state"""
    return request.app.state.config

# Type aliases for core dependencies
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[ServiceConfig, Depends(get_config)]

# Service dependencies
def get_prisma(lifecycle: LifecycleDep) -> Prisma:
    """Get Prisma client"""
    if not lifecycle.prisma:
        raise HTTPException(500, "Database not initialized")
    return lifecycle.prisma

def get_redis(lifecycle: LifecycleDep) -> redis.Redis:
    """Get Redis client"""
    if not lifecycle.redis:
        raise HTTPException(500, "Redis not initialized")
    return lifecycle.redis

def get_billing_service(lifecycle: LifecycleDep) -> BillingService:
    """Get billing service"""
    if not lifecycle.billing_service:
        raise HTTPException(500, f"{BillingService.__name__} not initialized")
    return lifecycle.billing_service

def get_webhook_service(lifecycle: LifecycleDep) -> WebhookProcessingService:
    """Get webhook processing service"""
    if not lifecycle.webhook_service:
        raise HTTPException(500, f"{WebhookProcessingService.__name__} not initialized")
    return lifecycle.webhook_service

def get_publisher(lifecycle: LifecycleDep) -> BillingEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "Event publisher not initialized")
    return lifecycle.event_publisher

# Type aliases
PrismaDep = Annotated[Prisma, Depends(get_prisma)]
RedisDep = Annotated[redis.Redis, Depends(get_redis)]
BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]
WebhookServiceDep = Annotated[WebhookProcessingService, Depends(get_webhook_service)]
PublisherDep = Annotated[BillingEventPublisher, Depends(get_publisher)]

# Header dependencies
def get_shop_domain(x_shop_domain: Optional[str] = Header(None)) -> str:
    """Get shop domain from header"""
    if not x_shop_domain:
        raise HTTPException(400, "Missing required header: X-Shop-Domain")
    return x_shop_domain

def get_idempotency_key(x_idempotency_key: Optional[str] = Header(None)) -> Optional[str]:
    """Get idempotency key from header"""
    return x_idempotency_key

def get_bearer_token(authorization: Optional[str] = Header(None)) -> str:
    """Get bearer token from authorization header"""
    if not authorization:
        raise HTTPException(401, "Invalid or missing authorization")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization format")
    
    return authorization[7:]  # Remove "Bearer " prefix

# Type aliases
ShopDomainDep = Annotated[str, Depends(get_shop_domain)]
IdempotencyKeyDep = Annotated[Optional[str], Depends(get_idempotency_key)]
BearerTokenDep = Annotated[str, Depends(get_bearer_token)]

# Auth dependencies
def verify_frontend_auth(token: BearerTokenDep, config: ConfigDep) -> None:
    """Verify frontend API key"""
    if token != config.billing_api_key:
        raise HTTPException(401, "Invalid or missing authorization")

def verify_admin_auth(token: BearerTokenDep, config: ConfigDep) -> None:
    """Verify admin API key"""
    if token != config.billing_admin_api_key:
        raise HTTPException(403, "Access forbidden")

# Type aliases
FrontendAuthDep = Annotated[None, Depends(verify_frontend_auth)]
AdminAuthDep = Annotated[None, Depends(verify_admin_auth)]

