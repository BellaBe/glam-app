# services/analytics/src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request, HTTPException
from shared.api.dependencies import (
    RequestContextDep,
    ClientAuthDep,
    PlatformContextDep,
    PaginationDep,
    LoggerDep
)
from .lifecycle import ServiceLifecycle
from .services.analytics_service import AnalyticsService
from .services.aggregation_service import AggregationService
from .config import ServiceConfig

# Re-export shared dependencies
__all__ = [
    "RequestContextDep",
    "ClientAuthDep",
    "PlatformContextDep",
    "PaginationDep",
    "LoggerDep",
    "LifecycleDep",
    "ConfigDep",
    "AnalyticsServiceDep",
    "AggregationServiceDep"
]

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
def get_analytics_service(lifecycle: LifecycleDep) -> AnalyticsService:
    """Get analytics service"""
    if not lifecycle.analytics_service:
        raise HTTPException(500, "Analytics service not initialized")
    return lifecycle.analytics_service

def get_aggregation_service(lifecycle: LifecycleDep) -> AggregationService:
    """Get aggregation service"""
    if not lifecycle.aggregation_service:
        raise HTTPException(500, "Aggregation service not initialized")
    return lifecycle.aggregation_service

AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
AggregationServiceDep = Annotated[AggregationService, Depends(get_aggregation_service)]