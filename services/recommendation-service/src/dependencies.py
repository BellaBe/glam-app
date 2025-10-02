# services/recommendation-service/src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request, HTTPException
from shared.api.dependencies import (
    RequestContextDep,
    ClientAuthDep,
    PlatformContextDep,
    PaginationDep,
    LoggerDep,
    CorrelationIdDep
)
from .lifecycle import ServiceLifecycle
from .services.recommendation_service import RecommendationService
from .events.publishers import RecommendationEventPublisher

# Re-export shared dependencies
__all__ = [
    "RequestContextDep",
    "ClientAuthDep", 
    "PlatformContextDep",
    "PaginationDep",
    "LoggerDep",
    "CorrelationIdDep",
    "LifecycleDep",
    "ConfigDep",
    "RecommendationServiceDep",
    "EventPublisherDep"
]


def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle


def get_config(request: Request):
    """Get service config from app state"""
    return request.app.state.config


LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[object, Depends(get_config)]


def get_recommendation_service(lifecycle: LifecycleDep) -> RecommendationService:
    """Get recommendation service"""
    if not lifecycle.recommendation_service:
        raise HTTPException(500, "Recommendation service not initialized")
    return lifecycle.recommendation_service


def get_event_publisher(lifecycle: LifecycleDep) -> RecommendationEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "Event publisher not initialized")
    return lifecycle.event_publisher


RecommendationServiceDep = Annotated[RecommendationService, Depends(get_recommendation_service)]
EventPublisherDep = Annotated[RecommendationEventPublisher, Depends(get_event_publisher)]