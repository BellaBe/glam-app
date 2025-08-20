# services/token-service/src/dependencies.py

from typing import Annotated
from fastapi import Depends, Request, HTTPException
from shared.api.dependencies import (
    RequestContextDep,
    ClientAuthDep,
    InternalAuthDep,
    LoggerDep,
    ClientIpDep
)
from .lifecycle import ServiceLifecycle
from .services.token_service import TokenService
from .config import ServiceConfig

# Re-export shared dependencies
__all__ = [
    "RequestContextDep",
    "ClientAuthDep",
    "InternalAuthDep",
    "LoggerDep",
    "ClientIpDep",
    "LifecycleDep",
    "ConfigDep",
    "TokenServiceDep"
]

def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle

def get_config(request: Request) -> ServiceConfig:
    """Get service config from app state"""
    return request.app.state.config

LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[ServiceConfig, Depends(get_config)]

def get_token_service(lifecycle: LifecycleDep) -> TokenService:
    """Get token service"""
    if not lifecycle.token_service:
        raise HTTPException(500, "Token service not initialized")
    return lifecycle.token_service

TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]