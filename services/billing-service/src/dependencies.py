# services/billing-service/src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request, HTTPException
import redis.asyncio as redis

from shared.messaging.jetstream_client import JetStreamWrapper
from .lifecycle import ServiceLifecycle
from .config import BillingServiceConfig

from .services import (
    BillingService,
    TrialService,
    OneTimePurchaseService,
)

from .repositories import (
    SubscriptionRepository,
    OneTimePurchaseRepository,
    BillingPlanRepository,
    TrialExtensionRepository,
)

from .events import BillingEventPublisher

from .mappers import (
    BillingPlanMapper,
    SubscriptionMapper,
    OneTimePurchaseMapper,
    TrialExtensionMapper,
)


def get_lifecycle(request: Request) -> ServiceLifecycle:
    return request.app.state.lifecycle


def get_config(request: Request) -> BillingServiceConfig:
    return request.app.state.config

# Type aliases for core dependencies
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[BillingServiceConfig, Depends(get_config)]

# Messaging dependencies
def get_messaging_wrapper(lifecycle: LifecycleDep) -> JetStreamWrapper:
    """Get messaging wrapper from lifecycle"""
    if not lifecycle.messaging_wrapper:
        raise HTTPException(500, "Messaging not initialized")
    return lifecycle.messaging_wrapper


def get_event_publisher(
    wrapper: Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)],
) -> BillingEventPublisher:
    """Get billing event publisher"""
    pub = wrapper.get_publisher(BillingEventPublisher)
    if not pub:
        raise HTTPException(500, "BillingEventPublisher not initialized")
    return pub

# Type aliases for messaging dependencies
MessagingDep = Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)]
PublisherDep = Annotated[BillingEventPublisher, Depends(get_event_publisher)]

# Repositories
def get_billing_plan_repository(
    lifecycle: LifecycleDep,
) -> BillingPlanRepository:
    """Get billing plan repository"""
    if not lifecycle.plan_repo:
        raise HTTPException(500, "BillingPlanRepository not initialized")
    return lifecycle.plan_repo

def get_subscription_repository(
    lifecycle: LifecycleDep,
) -> SubscriptionRepository:
    """Get subscription repository"""
    if not lifecycle.subscription_repo:
        raise HTTPException(500, "SubscriptionRepository not initialized")
    return lifecycle.subscription_repo

def get_one_time_purchase_repository(
    lifecycle: LifecycleDep,
) -> OneTimePurchaseRepository:
    """Get one-time purchase repository"""
    if not lifecycle.purchase_repo:
        raise HTTPException(500, "OneTimePurchaseRepository not initialized")
    return lifecycle.purchase_repo

def get_trial_extension_repository(
    lifecycle: LifecycleDep,
) -> TrialExtensionRepository:
    """Get trial extension repository"""
    if not lifecycle.extension_repo:
        raise HTTPException(500, "TrialExtensionRepository not initialized")
    return lifecycle.extension_repo

# Type aliases for repositories
BillingPlanRepoDep = Annotated[BillingPlanRepository, Depends(get_billing_plan_repository)]
SubscriptionRepoDep = Annotated[SubscriptionRepository, Depends(get_subscription_repository)]
OneTimePurchaseRepoDep = Annotated[OneTimePurchaseRepository, Depends(get_one_time_purchase_repository)]
TrialExtensionRepoDep = Annotated[TrialExtensionRepository, Depends(get_trial_extension_repository)]

# Services
def get_billing_service(lifecycle: LifecycleDep) -> BillingService:
    """Get billing service"""
    if not lifecycle.billing_service:
        raise HTTPException(500, "BillingService not initialized")
    return lifecycle.billing_service

def get_trial_service(lifecycle: LifecycleDep) -> TrialService: 
    """Get trial service"""
    if not lifecycle.trial_service:
        raise HTTPException(500, "TrialService not initialized")
    return lifecycle.trial_service

def get_one_time_purchase_service(lifecycle: LifecycleDep) -> OneTimePurchaseService:
    """Get one-time purchase service"""
    if not lifecycle.purchase_service:
        raise HTTPException(500, "OneTimePurchaseService not initialized")
    return lifecycle.purchase_service

# Type aliases for services
BillingServiceDep = Annotated[BillingService, Depends(get_billing_service)]
TrialServiceDep = Annotated[TrialService, Depends(get_trial_service)]
OneTimePurchaseServiceDep = Annotated[OneTimePurchaseService, Depends(get_one_time_purchase_service)]

# Mappers
def get_billing_plan_mapper() -> BillingPlanMapper:
    """Get billing plan mapper"""
    return BillingPlanMapper()
def get_subscription_mapper() -> SubscriptionMapper:
    """Get subscription mapper"""
    return SubscriptionMapper()
def get_one_time_purchase_mapper() -> OneTimePurchaseMapper:
    """Get one-time purchase mapper"""
    return OneTimePurchaseMapper()
def get_trial_extension_mapper() -> TrialExtensionMapper:
    """Get trial extension mapper"""
    return TrialExtensionMapper()   

# Type aliases for mappers
BillingPlanMapperDep = Annotated[BillingPlanMapper, Depends(get_billing_plan_mapper)]
SubscriptionMapperDep = Annotated[SubscriptionMapper, Depends(get_subscription_mapper)]
OneTimePurchaseMapperDep = Annotated[OneTimePurchaseMapper, Depends(get_one_time_purchase_mapper)]
TrialExtensionMapperDep = Annotated[TrialExtensionMapper, Depends(get_trial_extension_mapper)]


# Utility dependencies
def get_redis_client(lifecycle: LifecycleDep) -> redis.Redis:
    """Get Redis client"""
    if not lifecycle.redis_client:
        raise HTTPException(500, "Redis client not initialized")
    return lifecycle.redis_client

# Type alias for Redis client
RedisClientDep = Annotated[redis.Redis, Depends(get_redis_client)]
