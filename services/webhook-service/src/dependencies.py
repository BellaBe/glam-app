# services/webhook-service/src/dependencies.py
"""
FastAPI dependencies for webhook service.

Follows the same pattern as notification and credit services.
"""

from typing import Annotated, Any
from fastapi import Depends, Request, HTTPException
import redis.asyncio as redis

from shared.database.dependencies import DBSessionDep
from shared.messaging.jetstream_wrapper import JetStreamWrapper

from .lifecycle import ServiceLifecycle
from .services.webhook_service import WebhookService
from .services.platform_handler_service import PlatformHandlerService
from .repositories.webhook_entry_repository import WebhookEntryRepository
from .repositories.platform_configuration_repository import PlatformConfigurationRepository
from .events.publishers import WebhookEventPublisher
from .mappers.webhook_entry_mapper import WebhookEntryMapper


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


def get_publisher(
    wrapper: Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)],
) -> WebhookEventPublisher:
    """Get webhook event publisher"""
    pub = wrapper.get_publisher(WebhookEventPublisher)
    if not pub:
        raise HTTPException(500, "WebhookEventPublisher not initialized")
    return pub


# Type aliases for messaging
MessagingDep = Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)]
PublisherDep = Annotated[WebhookEventPublisher, Depends(get_publisher)]


# Repository dependencies
def get_webhook_entry_repo(lifecycle: LifecycleDep) -> WebhookEntryRepository:
    """Get webhook entry repository"""
    if not lifecycle.webhook_entry_repo:
        raise HTTPException(500, "WebhookEntryRepository not initialized")
    return lifecycle.webhook_entry_repo


def get_platform_config_repo(lifecycle: LifecycleDep) -> PlatformConfigurationRepository:
    """Get platform configuration repository"""
    if not lifecycle.platform_config_repo:
        raise HTTPException(500, "PlatformConfigurationRepository not initialized")
    return lifecycle.platform_config_repo


# Type aliases for repositories
WebhookEntryRepoDep = Annotated[WebhookEntryRepository, Depends(get_webhook_entry_repo)]
PlatformConfigRepoDep = Annotated[PlatformConfigurationRepository, Depends(get_platform_config_repo)]


# Service dependencies
def get_webhook_service(lifecycle: LifecycleDep) -> WebhookService:
    """Get webhook service"""
    if not lifecycle.webhook_service:
        raise HTTPException(500, "WebhookService not initialized")
    return lifecycle.webhook_service


def get_platform_handler_service(lifecycle: LifecycleDep) -> PlatformHandlerService:
    """Get platform handler service"""
    if not lifecycle.platform_handler_service:
        raise HTTPException(500, "PlatformHandlerService not initialized")
    return lifecycle.platform_handler_service


# Type aliases for services
WebhookServiceDep = Annotated[WebhookService, Depends(get_webhook_service)]
PlatformHandlerServiceDep = Annotated[PlatformHandlerService, Depends(get_platform_handler_service)]


# Mapper dependencies
def get_webhook_entry_mapper(lifecycle: LifecycleDep) -> WebhookEntryMapper:
    """Get webhook entry mapper"""
    if not lifecycle.webhook_entry_mapper:
        raise HTTPException(500, "WebhookEntryMapper not initialized")
    return lifecycle.webhook_entry_mapper


# Type aliases for mappers
WebhookEntryMapperDep = Annotated[WebhookEntryMapper, Depends(get_webhook_entry_mapper)]


# Redis dependency
def get_redis_client(lifecycle: LifecycleDep) -> redis.Redis:
    """Get Redis client"""
    if not lifecycle.redis_client:
        raise HTTPException(500, "Redis client not initialized")
    return lifecycle.redis_client


RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]