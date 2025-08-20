# services/season-compatibility/src/dependencies.py
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from shared.api.dependencies import CorrelationIdDep, LoggerDep, RequestContextDep

from .config import ServiceConfig
from .lifecycle import ServiceLifecycle
from .services.compatibility_service import CompatibilityService

# Re-export shared dependencies
__all__ = ["CompatibilityServiceDep", "ConfigDep", "CorrelationIdDep", "LifecycleDep", "LoggerDep", "RequestContextDep"]


# Core dependencies
def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle


def get_config(request: Request) -> ServiceConfig:
    """Get service config from app state"""
    return request.app.state.config


# Type aliases
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[ServiceConfig, Depends(get_config)]


# Service dependencies
def get_compatibility_service(lifecycle: LifecycleDep) -> CompatibilityService:
    """Get compatibility service"""
    if not lifecycle.compatibility_service:
        raise HTTPException(500, "Compatibility service not initialized")
    return lifecycle.compatibility_service


CompatibilityServiceDep = Annotated[CompatibilityService, Depends(get_compatibility_service)]
