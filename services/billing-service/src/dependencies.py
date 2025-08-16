# services/billing-service/src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request, HTTPException
from prisma import Prisma
from shared.api.dependencies import (
    RequestIdDep, PaginationDep, CorrelationIdDep, 
    RequestContextDep, PaginationParams
)
from .lifecycle import ServiceLifecycle
from .services.billing_service import BillingService
from .services.purchase_service import PurchaseService
from .events.publishers import BillingEventPublisher
from .config import ServiceConfig


# Re-export shared dependencies
__all__ = [
    "CorrelationIdDep", 
    "PaginationDep",
    "RequestIdDep",
    "RequestContextDep",
    "LifecycleDep",
    "ConfigDep",
    "BillingServiceDep",
    "PurchaseServiceDep",
    "PublisherDep"
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
def get_billing_service(lifecycle: LifecycleDep) -> BillingService:
    """Get billing service"""
    if not lifecycle.billing_service:
        raise HTTPException(500, "Billing service not initialized")
    return lifecycle.billing_service


def get_purchase_service(lifecycle: LifecycleDep) -> PurchaseService:
    """Get purchase service"""
    if not lifecycle.purchase_service:
        raise HTTPException(500, "Purchase service not initialized")
    return lifecycle.purchase_service


def get_publisher(lifecycle: LifecycleDep) -> BillingEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "Event publisher not initialized")
    return lifecycle.event_publisher


# Type aliases
BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]
PurchaseServiceDep = Annotated[PurchaseService, Depends(get_purchase_service)]
PublisherDep = Annotated[BillingEventPublisher, Depends(get_publisher)]
