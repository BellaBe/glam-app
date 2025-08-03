from typing import Annotated
from fastapi import Depends, Request, HTTPException, status
from shared.api.dependencies import (
    RequestIdDep, PaginationDep, CorrelationIdDep, RequestContextDep
)
from .lifecycle import ServiceLifecycle
from .config import ServiceConfig
from .services import MerchantService

__all__ = [
    "CorrelationIdDep",
    "PaginationDep",
    "RequestIdDep",
    "RequestContextDep",
    "LifecycleDep",
    "ConfigDep",
    "MerchantServiceDep",
]

# Core dependencies
def get_lifecycle(request: Request) -> ServiceLifecycle:
    lc = getattr(request.app.state, "lifecycle", None)
    if lc is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Lifecycle not initialized")
    return lc

def get_config(request: Request) -> ServiceConfig:
    cfg = getattr(request.app.state, "config", None)
    if cfg is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Config not initialized")
    return cfg

LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[ServiceConfig, Depends(get_config)]

def get_merchant_service(lifecycle: LifecycleDep) -> MerchantService:
    svc = lifecycle.merchant_service
    if svc is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "MerchantService not initialized")
    return svc

MerchantServiceDep = Annotated[MerchantService, Depends(get_merchant_service)]
