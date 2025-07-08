# services/webhook-service/src/dependencies.py
"""
FastAPI dependencies for webhook service.

Follows the same pattern as notification service.
"""

from typing import Annotated, Any
from fastapi import Depends, Request, HTTPException

from shared.database.dependencies import DBSessionDep
from shared.messaging.jetstream_wrapper import JetStreamWrapper

from .lifecycle import ServiceLifecycle
from .services.webhook_service import WebhookService
from .services.auth_service import WebhookAuthService
from .services.deduplication_service import DeduplicationService
from .services.circuit_breaker_service import CircuitBreakerService
from .repositories.webhook_repository import WebhookRepository
from .repositories.platform_config_repository import PlatformConfigRepository
from .events.publishers import WebhookEventPublisher


# Core dependencies
def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle


def get_config(request: Request):
    """Get service config from app state"""
    return request.app.state.config


# Type aliases for core dependencies
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[Any, Depends(get_config)]


# Messaging dependencies
def get_messaging_wrapper(lifecycle: LifecycleDep) -> JetStreamWrapper:
    """Get messaging wrapper"""
    if not lifecycle.messaging_wrapper:
        raise HTTPException(500, "Messaging not initialized")
    return lifecycle.messaging_wrapper


def get_publisher(wrapper: Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)]) -> WebhookEventPublisher:
    """Get webhook event publisher"""
    pub = wrapper.get_publisher(WebhookEventPublisher)
    if not pub:
        raise HTTPException(500, "WebhookEventPublisher not initialized")
    return pub


# Type aliases for messaging
MessagingDep = Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)]
PublisherDep = Annotated[WebhookEventPublisher, Depends(get_publisher)]


# Repository dependencies
def get_webhook_repo(lifecycle: LifecycleDep) -> WebhookRepository:
    """Get webhook repository"""
    if not lifecycle.webhook_repo:
        raise HTTPException(500, "WebhookRepository not initialized")
    return lifecycle.webhook_repo


def get_platform_config_repo(lifecycle: LifecycleDep) -> PlatformConfigRepository:
    """Get platform config repository"""
    if not lifecycle.platform_config_repo:
        raise HTTPException(500, "PlatformConfigRepository not initialized")
    return lifecycle.platform_config_repo


# Type aliases for repositories
WebhookRepoDep = Annotated[WebhookRepository, Depends(get_webhook_repo)]
PlatformConfigRepoDep = Annotated[PlatformConfigRepository, Depends(get_platform_config_repo)]


# Service dependencies
def get_auth_service(lifecycle: LifecycleDep) -> WebhookAuthService:
    """Get auth service"""
    if not lifecycle.auth_service:
        raise HTTPException(500, "AuthService not initialized")
    return lifecycle.auth_service


def get_dedup_service(lifecycle: LifecycleDep) -> DeduplicationService:
    """Get deduplication service"""
    if not lifecycle.dedup_service:
        raise HTTPException(500, "DeduplicationService not initialized")
    return lifecycle.dedup_service


def get_circuit_breaker(lifecycle: LifecycleDep) -> CircuitBreakerService:
    """Get circuit breaker service"""
    if not lifecycle.circuit_breaker:
        raise HTTPException(500, "CircuitBreakerService not initialized")
    return lifecycle.circuit_breaker


def get_webhook_service(lifecycle: LifecycleDep) -> WebhookService:
    """Get webhook service"""
    if not lifecycle.webhook_service:
        raise HTTPException(500, "WebhookService not initialized")
    return lifecycle.webhook_service


# Type aliases for services
AuthServiceDep = Annotated[WebhookAuthService, Depends(get_auth_service)]
DedupServiceDep = Annotated[DeduplicationService, Depends(get_dedup_service)]
CircuitBreakerDep = Annotated[CircuitBreakerService, Depends(get_circuit_breaker)]
WebhookServiceDep = Annotated[WebhookService, Depends(get_webhook_service)]