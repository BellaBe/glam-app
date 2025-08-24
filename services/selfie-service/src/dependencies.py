# services/selfie-service/src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request, HTTPException
from shared.api.dependencies import (
    RequestContextDep,
    PlatformContextDep,
    PaginationDep,
    LoggerDep,
    ClientAuthContext
)
import jwt
import os
from .lifecycle import ServiceLifecycle
from .services.selfie_service import SelfieService
from .services.image_processor import ImageProcessor
from .events.publishers import SelfieEventPublisher
from .config import ServiceConfig

# Re-export shared dependencies for convenience
__all__ = [
    "RequestContextDep",
    "PlatformContextDep",
    "PaginationDep",
    "LoggerDep",
    "ClientAuthDep",
    "LifecycleDep",
    "ConfigDep",
    "SelfieServiceDep",
    "ImageProcessorDep",
    "EventPublisherDep"
]

# Custom ClientAuth with additional fields for selfie service
class ExtendedClientAuthContext(ClientAuthContext):
    """Extended auth context with merchant and platform info"""
    merchant_id: str
    platform_shop_id: str
    platform_domain: str

def require_extended_client_auth(request: Request) -> ExtendedClientAuthContext:
    """
    Client authentication with extended merchant context.
    JWT must contain: merchant_id, platform_name, platform_shop_id, platform_domain
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    
    token = auth.split(" ", 1)[1].strip()
    secret = os.getenv("CLIENT_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("CLIENT_JWT_SECRET not configured")
    
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        
        # Validate required fields
        required_fields = ["sub", "scope", "merchant_id", "platform_shop_id", "platform_domain"]
        for field in required_fields:
            if field not in payload:
                raise HTTPException(
                    status_code=401,
                    detail=f"JWT missing required field: {field}"
                )
        
        # Check expiration (max 5 minutes)
        import time
        if "exp" in payload:
            if payload["exp"] < time.time():
                raise HTTPException(status_code=401, detail="TOKEN_EXPIRED")
        
        return ExtendedClientAuthContext(
            shop=payload["sub"],  # This should be platform_domain
            scope=payload["scope"],
            token=token,
            merchant_id=payload["merchant_id"],
            platform_shop_id=payload["platform_shop_id"],
            platform_domain=payload["platform_domain"]
        )
        
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid JWT: {str(e)}")

ClientAuthDep = Annotated[ExtendedClientAuthContext, Depends(require_extended_client_auth)]

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
def get_selfie_service(lifecycle: LifecycleDep) -> SelfieService:
    """Get selfie service"""
    if not lifecycle.selfie_service:
        raise HTTPException(500, "Selfie service not initialized")
    return lifecycle.selfie_service

def get_image_processor(lifecycle: LifecycleDep) -> ImageProcessor:
    """Get image processor"""
    if not lifecycle.image_processor:
        raise HTTPException(500, "Image processor not initialized")
    return lifecycle.image_processor

def get_event_publisher(lifecycle: LifecycleDep) -> SelfieEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "Event publisher not initialized")
    return lifecycle.event_publisher

SelfieServiceDep = Annotated[SelfieService, Depends(get_selfie_service)]
ImageProcessorDep = Annotated[ImageProcessor, Depends(get_image_processor)]
EventPublisherDep = Annotated[SelfieEventPublisher, Depends(get_event_publisher)]