# services/credit-service/src/dependencies.py
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from shared.api.dependencies import (
    ClientAuthDep,
    LoggerDep,
    PaginationDep,
    PlatformContextDep,
    RequestContextDep,
)

from .config import ServiceConfig
from .lifecycle import ServiceLifecycle
from .services.credit_service import CreditService

# Re-export shared dependencies
__all__ = [
    "ClientAuthDep",
    "ConfigDep",
    "CreditServiceDep",
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


def get_config(request: Request):
    """Get service config from app state"""
    return request.app.state.config


# Type aliases
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[ServiceConfig, Depends(get_config)]


# Service dependencies
def get_credit_service(lifecycle: LifecycleDep) -> CreditService:
    """Get credit service"""
    if not lifecycle.credit_service:
        raise HTTPException(500, "Credit service not initialized")
    return lifecycle.credit_service


CreditServiceDep = Annotated[CreditService, Depends(get_credit_service)]
