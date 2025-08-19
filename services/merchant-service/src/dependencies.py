from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from shared.api.dependencies import CorrelationIdDep, PaginationDep, RequestContextDep, RequestIdDep

from .config import ServiceConfig
from .lifecycle import ServiceLifecycle
from .services import MerchantService

__all__ = [
    "ConfigDep",
    "CorrelationIdDep",
    "LifecycleDep",
    "MerchantServiceDep",
    "PaginationDep",
    "RequestContextDep",
    "RequestIdDep",
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
