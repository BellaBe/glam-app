from typing import Annotated
from fastapi import Depends, Request, HTTPException
from prisma import Prisma
import redis.asyncio as redis
from shared.api.dependencies import RequestIdDep, PaginationDep, CorrelationIdDep, RequestContextDep
from shared.messaging.jetstream_client import JetStreamClient
from .lifecycle import ServiceLifecycle
from .config import ServiceConfig, get_service_config
from .services.webhook_service import WebhookService
from .services.webhook_processor import WebhookProcessor
from .events.publishers import WebhookEventPublisher


# Re-export shared dependencies
__all__ = [
    "PrismaDep",
    "RedisClientDep",
    "CorrelationIdDep", 
    "PaginationDep",
    "RequestIdDep",
    "RequestContextDep",
    "LifecycleDep",
    "ConfigDep",
    "WebhookServiceDep",
    "WebhookProcessorDep",
    "PublisherDep"
]


# Core dependencies
def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle


def get_config(request: Request) -> ServiceConfig:
    """Get service config from app state"""
    return request.app.state.config


# Type aliases for core dependencies
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[ServiceConfig, Depends(get_config)]

# Service dependencies
def get_webhook_service(lifecycle: LifecycleDep) -> WebhookService:
    """Get webhook service"""
    if not lifecycle.webhook_service:
        raise HTTPException(500, "Webhook service not initialized")
    return lifecycle.webhook_service


def get_webhook_processor(lifecycle: LifecycleDep) -> WebhookProcessor:
    """Get webhook processor"""
    if not lifecycle.webhook_processor:
        raise HTTPException(500, "Webhook processor not initialized")
    return lifecycle.webhook_processor


# Type aliases
WebhookServiceDep = Annotated[WebhookService, Depends(get_webhook_service)]
WebhookProcessorDep = Annotated[WebhookProcessor, Depends(get_webhook_processor)]


