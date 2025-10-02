# services/platform-connector/src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request, HTTPException

# Re-export shared dependencies
from shared.api.dependencies import (
    RequestContextDep,
    LoggerDep
)

from .lifecycle import ServiceLifecycle
from .services.connector_service import ConnectorService
from .events.publishers import PlatformEventPublisher

__all__ = [
    "RequestContextDep",
    "LoggerDep",
    "LifecycleDep",
    "ConnectorServiceDep",
    "EventPublisherDep"
]

# Core dependencies
def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle

LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]

def get_connector_service(lifecycle: LifecycleDep = Depends(get_lifecycle)) -> ConnectorService:
    """Get connector service"""
    if not lifecycle.connector_service:
        raise HTTPException(500, "Connector service not initialized")
    return lifecycle.connector_service

def get_event_publisher(lifecycle: LifecycleDep = Depends(get_lifecycle)) -> PlatformEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "Event publisher not initialized")
    return lifecycle.event_publisher

# Type aliases

ConnectorServiceDep = Annotated[ConnectorService, Depends(get_connector_service)]
EventPublisherDep = Annotated[PlatformEventPublisher, Depends(get_event_publisher)]