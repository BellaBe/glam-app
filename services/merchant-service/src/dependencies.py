# services/merchant-service/src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request, HTTPException
from shared.api.dependencies import RequestIdDep, PaginationDep, CorrelationIdDep
from shared.database.dependencies import DBSessionDep
from .lifecycle import ServiceLifecycle
from .services.merchant import MerchantService
from .events.publishers import MerchantEventPublisher

# Re-export shared dependencies
__all__ = [
    "DBSessionDep",
    "CorrelationIdDep", 
    "PaginationDep",
    "RequestIdDep",
    "LifecycleDep",
    "ConfigDep",
    "MerchantServiceDep",
    "PublisherDep"
]

# Core dependencies
def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle

def get_config(request: Request):
    """Get service config from app state"""
    return request.app.state.config

# Type aliases for core dependencies
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[object, Depends(get_config)]

# Service dependencies
def get_merchant_service(lifecycle: LifecycleDep) -> MerchantService:
    """Get merchant service"""
    if not lifecycle.merchant_service:
        raise HTTPException(500, f"{MerchantService.__name__} not initialized")
    return lifecycle.merchant_service

def get_publisher(lifecycle: LifecycleDep) -> MerchantEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "EventPublisher not initialized")
    return lifecycle.event_publisher

# Type aliases
MerchantServiceDep = Annotated[MerchantService, Depends(get_merchant_service)]
PublisherDep = Annotated[MerchantEventPublisher, Depends(get_publisher)]
