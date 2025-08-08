from typing import Annotated, Optional
from fastapi import Depends, Request, HTTPException, Header
import redis.asyncio as redis
from prisma import Prisma
from shared.api.dependencies import RequestIdDep, PaginationDep, CorrelationIdDep, RequestContextDep
from .config import ServiceConfig
from .lifecycle import ServiceLifecycle
from .services.credit_service import CreditService
from .events.publishers import CreditEventPublisher

# Re-export shared dependencies
__all__ = [
    "CorrelationIdDep", 
    "PaginationDep",
    "RequestIdDep",
    "RequestContextDep",
    "LifecycleDep",
    "ConfigDep",
    "CreditServiceDep",
    "PublisherDep",
    "ShopDomainDep",
    "AdminAuthDep"
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
def get_credit_service(lifecycle: LifecycleDep) -> CreditService:
    """Get credit service"""
    if not lifecycle.credit_service:
        raise HTTPException(500, f"{CreditService.__name__} not initialized")
    return lifecycle.credit_service

def get_publisher(lifecycle: LifecycleDep) -> CreditEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "Event publisher not initialized")
    return lifecycle.event_publisher

# Shop domain header dependency
def get_shop_domain(
    x_shop_domain: Optional[str] = Header(None, alias="X-Shop-Domain")
) -> str:
    """Extract shop domain from header"""
    if not x_shop_domain:
        raise HTTPException(400, "Missing X-Shop-Domain header")
    return x_shop_domain

# Admin auth dependency (simplified for now)
def validate_admin_auth(
    authorization: Optional[str] = Header(None)
) -> str:
    """Validate admin bearer token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid bearer token")
    
    # TODO: Implement proper token validation
    # For now, just check presence
    token = authorization.replace("Bearer ", "")
    if not token:
        raise HTTPException(401, "Invalid bearer token")
    
    return token

# Type aliases
CreditServiceDep = Annotated[CreditService, Depends(get_credit_service)]
PublisherDep = Annotated[CreditEventPublisher, Depends(get_publisher)]
ShopDomainDep = Annotated[str, Depends(get_shop_domain)]
AdminAuthDep = Annotated[str, Depends(validate_admin_auth)]

