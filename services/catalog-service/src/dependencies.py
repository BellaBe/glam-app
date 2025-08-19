# services/catalog-service/src/dependencies.py
from typing import Annotated

from fastapi import Depends, HTTPException, Request

# Re-export shared dependencies
from shared.api.dependencies import (
    ClientAuthDep,
    LoggerDep,
    PaginationDep,
    PlatformContextDep,
    RequestContextDep,
)

from .events.publishers import CatalogEventPublisher
from .lifecycle import ServiceLifecycle
from .services.catalog_service import CatalogService

__all__ = [
    "CatalogServiceDep",
    "ClientAuthDep",
    "EventPublisherDep",
    "LifecycleDep",
    "LoggerDep",
    "PaginationDep",
    "PlatformContextDep",
    "RequestContextDep",
]


# Core dependencies
def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle


LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]


def get_catalog_service(
    lifecycle: LifecycleDep = Depends(get_lifecycle),
) -> CatalogService:
    """Get catalog service"""
    if not lifecycle.catalog_service:
        raise HTTPException(500, "Catalog service not initialized")
    return lifecycle.catalog_service


def get_event_publisher(
    lifecycle: LifecycleDep = Depends(get_lifecycle),
) -> CatalogEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "Event publisher not initialized")
    return lifecycle.event_publisher


# Type aliases

CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
EventPublisherDep = Annotated[CatalogEventPublisher, Depends(get_event_publisher)]
