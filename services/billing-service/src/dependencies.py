from __future__ import annotations

from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request, status


def get_lifecycle(request: Request):
    lc = getattr(request.app.state, "lifecycle", None)
    if lc is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Lifecycle not initialized")
    return lc


def get_config(request: Request):
    cfg = getattr(request.app.state, "config", None)
    if cfg is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Config not initialized")
    return cfg


LifecycleDep = Annotated[Any, Depends(get_lifecycle)]
ConfigDep = Annotated[Any, Depends(get_config)]


def get_billing_service(lifecycle: LifecycleDep):
    svc = lifecycle.billing_service
    if svc is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "BillingService not initialized")
    return svc


BillingServiceDep = Annotated[Any, Depends(get_billing_service)]
