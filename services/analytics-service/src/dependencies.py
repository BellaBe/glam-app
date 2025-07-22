from typing import Annotated
from fastapi import Depends, Request, HTTPException
from shared.api.dependencies import RequestIdDep, PaginationDep, CorrelationIdDep
from shared.database.dependencies import DBSessionDep
from .lifecycle import AnalyticsLifecycle
from .config import AnalyticsConfig
from .services.analytics_service import AnalyticsService
from .services.alert_service import AlertService
from .services.pattern_detection_service import PatternDetectionService
from .services.prediction_service import PredictionService
from .events.publishers import AnalyticsEventPublisher

# Re-export shared dependencies
__all__ = [
    "DBSessionDep",
    "CorrelationIdDep",
    "PaginationDep", 
    "RequestIdDep",
    "LifecycleDep",
    "ConfigDep",
    "AnalyticsServiceDep",
    "AlertServiceDep",
    "PatternServiceDep",
    "PredictionServiceDep",
    "PublisherDep"
]

# Core dependencies
def get_lifecycle(request: Request) -> AnalyticsLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle

def get_config(request: Request) -> AnalyticsConfig:
    """Get service config from app state"""
    return request.app.state.config

# Type aliases for core dependencies
LifecycleDep = Annotated[AnalyticsLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[AnalyticsConfig, Depends(get_config)]

# Service dependencies
def get_analytics_service(lifecycle: LifecycleDep) -> AnalyticsService:
    """Get analytics service"""
    if not lifecycle.analytics_service:
        raise HTTPException(500, "AnalyticsService not initialized")
    return lifecycle.analytics_service

def get_alert_service(lifecycle: LifecycleDep) -> AlertService:
    """Get alert service"""
    if not lifecycle.alert_service:
        raise HTTPException(500, "AlertService not initialized") 
    return lifecycle.alert_service

def get_pattern_service(lifecycle: LifecycleDep) -> PatternDetectionService:
    """Get pattern detection service"""
    if not lifecycle.pattern_service:
        raise HTTPException(500, "PatternDetectionService not initialized")
    return lifecycle.pattern_service

def get_prediction_service(lifecycle: LifecycleDep) -> PredictionService:
    """Get prediction service"""
    if not lifecycle.prediction_service:
        raise HTTPException(500, "PredictionService not initialized")
    return lifecycle.prediction_service

def get_publisher(lifecycle: LifecycleDep) -> AnalyticsEventPublisher:
    """Get event publisher"""
    if not lifecycle.event_publisher:
        raise HTTPException(500, "EventPublisher not initialized")
    return lifecycle.event_publisher

# Type aliases
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(get_analytics_service)]
AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
PatternServiceDep = Annotated[PatternDetectionService, Depends(get_pattern_service)]
PredictionServiceDep = Annotated[PredictionService, Depends(get_prediction_service)]
PublisherDep = Annotated[AnalyticsEventPublisher, Depends(get_publisher)]


