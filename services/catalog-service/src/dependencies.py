# src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request, HTTPException, Header
from shared.api.dependencies import RequestIdDep, PaginationDep, CorrelationIdDep
from shared.database.dependencies import DBSessionDep
from .lifecycle import CatalogServiceLifecycle
from .services.sync_service import SyncService
from .services.catalog_service import CatalogService
from .events.publishers import CatalogEventPublisher

# Re-export shared dependencies
__all__ = [
    "DBSessionDep",
    "CorrelationIdDep", 
    "PaginationDep",
    "RequestIdDep",
    "LifecycleDep",
    "ConfigDep",
    "SyncServiceDep",
    "CatalogServiceDep",
    "PublisherDep",
    "IdempotencyKeyDep"
]

def get_lifecycle(request: Request) -> CatalogServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle

def get_config(request: Request):
    """Get service config from app state"""
    return request.app.state.config

def get_idempotency_key(
    idempotency_key: str = Header(..., alias="Idempotency-Key")
) -> str:
    """Extract and validate idempotency key"""
    return idempotency_key

# Type aliases
LifecycleDep = Annotated[CatalogServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[CatalogServiceConfig, Depends(get_config)]
IdempotencyKeyDep = Annotated[str, Depends(get_idempotency_key)]

# Service dependencies
def get_sync_service(lifecycle: LifecycleDep) -> SyncService:
    """Get sync service"""
    if not lifecycle.sync_service:
        raise HTTPException(500, "SyncService not initialized")
    return lifecycle.sync_service

def get_catalog_service(lifecycle: LifecycleDep) -> CatalogService:
    """Get catalog service"""
    if not lifecycle.catalog_service:
        raise HTTPException(500, "CatalogService not initialized")
    return lifecycle.catalog_service

def get_publisher(lifecycle: LifecycleDep) -> CatalogEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "EventPublisher not initialized")
    return lifecycle.event_publisher

# Type aliases
SyncServiceDep = Annotated[SyncService, Depends(get_sync_service)]
CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
PublisherDep = Annotated[CatalogEventPublisher, Depends(get_publisher)]
