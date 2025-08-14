from typing import Annotated
from fastapi import Depends, Request, HTTPException, status
from .lifecycle import ServiceLifecycle
from .config import ServiceConfig
from .services import WebhookService

__all__ = [
    "LifecycleDep",
    "ConfigDep",
    "WebhookServiceDep",
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

# Type aliases
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[ServiceConfig, Depends(get_config)]

# Service dependencies
def get_webhook_service(lifecycle: LifecycleDep) -> WebhookService:
    """Get webhook service"""
    if not lifecycle.webhook_service:
        raise HTTPException(500, "Webhook service not initialized")
    return lifecycle.webhook_service

# Type aliases
WebhookServiceDep = Annotated[WebhookService, Depends(get_webhook_service)]


