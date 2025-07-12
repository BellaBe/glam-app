# services/credit-service/src/dependencies.py
"""
FastAPI dependencies for credit service.

Follows the same pattern as notification service.
"""

from typing import Annotated, Any
from fastapi import Depends, Request, HTTPException
import redis.asyncio as redis

from shared.database.dependencies import DBSessionDep
from shared.messaging.jetstream_wrapper import JetStreamWrapper

from .lifecycle import ServiceLifecycle
from .services.credit_service import CreditService
from .services.balance_monitor_service import BalanceMonitorService
from .services.plugin_status_service import PluginStatusService
from .services.credit_transaction_service import CreditTransactionService

from .repositories.credit_repository import CreditRepository
from .repositories.credit_transaction_repository import CreditTransactionRepository

from .events.publishers import CreditEventPublisher
from .mappers.credit_mapper import CreditMapper
from .mappers.credit_transaction_mapper import CreditTransactionMapper


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
) -> CreditEventPublisher:
    """Get credit event publisher"""
    pub = wrapper.get_publisher(CreditEventPublisher)
    if not pub:
        raise HTTPException(500, "CreditEventPublisher not initialized")
    return pub


# Type aliases for messaging
MessagingDep = Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)]
PublisherDep = Annotated[CreditEventPublisher, Depends(get_publisher)]


# Repository dependencies
def get_credit_repo(lifecycle: LifecycleDep) -> CreditRepository:
    """Get credit account repository"""
    if not lifecycle.credit_repo:
        raise HTTPException(500, "CreditRepository not initialized")
    return lifecycle.credit_repo


def get_credit_transaction_repo(lifecycle: LifecycleDep) -> CreditTransactionRepository:
    """Get credit transaction repository"""
    if not lifecycle.credit_transaction_repo:
        raise HTTPException(500, "CreditTransactionRepository not initialized")
    return lifecycle.credit_transaction_repo


# Type aliases for repositories
CreditRepoDep = Annotated[CreditRepository, Depends(get_credit_repo)]
CreditTransactionRepoDep = Annotated[
    CreditTransactionRepository, Depends(get_credit_transaction_repo)
]


# Service dependencies
def get_credit_service(lifecycle: LifecycleDep) -> CreditService:
    """Get credit service"""
    if not lifecycle.credit_service:
        raise HTTPException(500, "CreditService not initialized")
    return lifecycle.credit_service


def get_balance_monitor_service(lifecycle: LifecycleDep) -> BalanceMonitorService:
    """Get balance monitor service"""
    if not lifecycle.balance_monitor_service:
        raise HTTPException(500, "BalanceMonitorService not initialized")
    return lifecycle.balance_monitor_service


def get_plugin_status_service(lifecycle: LifecycleDep) -> PluginStatusService:
    """Get plugin status service"""
    if not lifecycle.plugin_status_service:
        raise HTTPException(500, "PluginStatusService not initialized")
    return lifecycle.plugin_status_service


def get_credit_transaction_service(
    lifecycle: LifecycleDep,
) -> CreditTransactionService:
    """Get credit transaction service"""
    if not lifecycle.credit_transaction_service:
        raise HTTPException(500, "CreditTransactionService not initialized")
    return lifecycle.credit_transaction_service


# Type aliases for services
CreditServiceDep = Annotated[CreditService, Depends(get_credit_service)]
BalanceMonitorServiceDep = Annotated[
    BalanceMonitorService, Depends(get_balance_monitor_service)
]
PluginStatusServiceDep = Annotated[
    PluginStatusService, Depends(get_plugin_status_service)
]

CreditTransactionServiceDep = Annotated[
    CreditTransactionService, Depends(get_credit_transaction_service)
]


# Utility dependencies
def get_redis_client(lifecycle: LifecycleDep) -> redis.Redis:
    """Get Redis client"""
    if not lifecycle.redis_client:
        raise HTTPException(500, "Redis client not initialized")
    return lifecycle.redis_client


def get_credit_mapper(lifecycle: LifecycleDep) -> CreditMapper:
    """Get credit account mapper"""
    if not lifecycle.credit_mapper:
        raise HTTPException(500, "CreditMapper not initialized")
    return lifecycle.credit_mapper


def get_credit_transaction_mapper(lifecycle: LifecycleDep) -> CreditTransactionMapper:
    """Get credit transaction mapper"""
    if not lifecycle.credit_transaction_mapper:
        raise HTTPException(500, "CreditTransactionMapper not initialized")
    return lifecycle.credit_transaction_mapper


# Type aliases for utilities
RedisClientDep = Annotated[redis.Redis, Depends(get_redis_client)]
CreditMapperDep = Annotated[CreditMapper, Depends(get_credit_mapper)]
CreditTransactionMapperDep = Annotated[
    CreditTransactionMapper, Depends(get_credit_transaction_mapper)
]
