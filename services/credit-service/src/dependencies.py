from typing import Annotated
from fastapi import Depends, HTTPException, Request, status
from .config import ServiceConfig
from .lifecycle import ServiceLifecycle
from .services.credit_service import CreditService


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


def get_credit_service(lifecycle: LifecycleDep) -> CreditService:
    svc = lifecycle.credit_service
    if not svc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "CreditService not initialized")
    return svc


CreditServiceDep = Annotated[CreditService, Depends(get_credit_service)]