# services/notification-service/src/dependencies.py
from typing import Annotated

from fastapi import Depends, HTTPException, Request

from .config import ServiceConfig
from .lifecycle import ServiceLifecycle
from .services.notification_service import NotificationService


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
def get_notification_service(lifecycle: LifecycleDep) -> NotificationService:
    """Get notification service"""
    if not lifecycle.notification_service:
        raise HTTPException(500, "Notification service not initialized")
    return lifecycle.notification_service


NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
