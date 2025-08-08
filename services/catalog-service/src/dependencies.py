from typing import Annotated
from fastapi import Depends, Request, HTTPException, Header
from shared.api.dependencies import RequestIdDep, PaginationDep, CorrelationIdDep, RequestContextDep
from .lifecycle import ServiceLifecycle
from .config import ServiceConfig
from .services.catalog_sync_service import CatalogSyncService
from .events.publishers import CatalogEventPublisher

# Re-export shared dependencies
__all__ = [
    "CorrelationIdDep", 
    "PaginationDep",
    "RequestIdDep",
    "RequestContextDep",
    "LifecycleDep",
    "ConfigDep",
    "CatalogSyncServiceDep",
    "PublisherDep",
    "AuthDep",
    "ShopDomainDep"
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
def get_catalog_sync_service(lifecycle: LifecycleDep) -> CatalogSyncService:
    """Get catalog sync service"""
    if not lifecycle.catalog_sync_service:
        raise HTTPException(500, f"{CatalogSyncService.__name__} not initialized")
    return lifecycle.catalog_sync_service

def get_publisher(lifecycle: LifecycleDep) -> CatalogEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "Event publisher not initialized")
    return lifecycle.event_publisher

# Type aliases
CatalogSyncServiceDep = Annotated[CatalogSyncService, Depends(get_catalog_sync_service)]
PublisherDep = Annotated[CatalogEventPublisher, Depends(get_publisher)]

# Auth dependencies
async def verify_auth(
    authorization: Annotated[str, Header()],
    config: ConfigDep
) -> str:
    """Verify Bearer token authentication"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    if token != config.app_api_key:
        raise HTTPException(401, "Invalid API key")
    
    return token

async def get_shop_domain(
    x_shop_domain: Annotated[str, Header(alias="X-Shop-Domain")]
) -> str:
    """Extract and validate shop domain from header"""
    if not x_shop_domain:
        raise HTTPException(400, "X-Shop-Domain header required")
    
    # Basic validation
    if not x_shop_domain.endswith(".myshopify.com"):
        raise HTTPException(400, "Invalid shop domain format")
    
    return x_shop_domain.lower()

AuthDep = Annotated[str, Depends(verify_auth)]
ShopDomainDep = Annotated[str, Depends(get_shop_domain)]

# ================================================================
