# File: services/notification-service/src/dependencies.py
"""
FastAPI dependency providers.
Each function merely returns a singleton already created
by ServiceLifecycle – *never* create new heavy objects here.
"""
from typing import Annotated
from fastapi import Depends, Request, HTTPException

from shared.api.dependencies import RequestIdDep, RequestContextDep, PaginationDep
from shared.api.correlation  import CorrelationIdDep

from shared.messaging.jetstream_wrapper import JetStreamWrapper
from .lifecycle        import ServiceLifecycle
from .services.notification_service import NotificationService
from .services.template_service     import TemplateService
from .services.email_service        import EmailService
from .services.preference_service   import PreferenceService
from .services.rate_limit_service   import InMemoryRateLimitService
from .events.publishers             import NotificationEventPublisher
from .utils.template_engine         import TemplateEngine

# ---------------------------------------------------------------- shared --- #
__all__ = [
    "RequestIdDep", "RequestContextDep", "PaginationDep", "CorrelationIdDep",
    "get_lifecycle", "get_config", "get_messaging_wrapper",
    "get_publisher", "get_rate_limit_service", "get_email_service",
    "get_template_engine", "get_template_service",
    "get_preference_service", "get_notification_service",
]

# --------------------------- core singletons via lifecycle ----------------- #
def get_lifecycle(request: Request) -> ServiceLifecycle:
    return request.app.state.lifecycle                 

def get_config(request: Request):
    return request.app.state.config                   

# ------------------------------- messaging --------------------------------- #
def get_messaging_wrapper(
    lc: Annotated[ServiceLifecycle, Depends(get_lifecycle)]
) -> JetStreamWrapper:
    if not lc.messaging_wrapper:
        raise HTTPException(500, "Messaging not initialised")
    return lc.messaging_wrapper

def get_publisher(
    wrapper: Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)]
) -> NotificationEventPublisher:
    pub = wrapper.get_publisher(NotificationEventPublisher)
    if not pub:
        raise HTTPException(500, "NotificationEventPublisher not initialised")
    return pub

# --------------------------------- utils ----------------------------------- #

def get_template_engine(
    lc: Annotated[ServiceLifecycle, Depends(get_lifecycle)]
) -> TemplateEngine:
    if not lc.template_engine:
        raise HTTPException(500, "TemplateEngine not initialised")
    return lc.template_engine

def get_email_service(
    lc: Annotated[ServiceLifecycle, Depends(get_lifecycle)]
) -> EmailService:
    """Get email service instance"""
    if not lc.email_service:
        raise HTTPException(500, "EmailService not initialised")
    return lc.email_service

def get_rate_limit_service(
    lc: Annotated[ServiceLifecycle, Depends(get_lifecycle)]
) -> InMemoryRateLimitService:
    """Get rate limit service instance"""
    if not lc.rate_limit_service:
        raise HTTPException(500, "RateLimitService not initialised")
    return lc.rate_limit_service


# --------------------------- domain services ------------------------------- #
def get_template_service(
    lc: Annotated[ServiceLifecycle, Depends(get_lifecycle)]
) -> TemplateService:
    """Get template service instance"""
    if not lc.template_service:
        raise HTTPException(500, "TemplateService not initialised")
    return lc.template_service

def get_preference_service(
    lc: Annotated[ServiceLifecycle, Depends(get_lifecycle)]
) -> PreferenceService:
    """Get preference service instance"""
    if not lc.preference_service:
        raise HTTPException(500, "PreferenceService not initialised")
    return lc.preference_service

def get_notification_service(
    lc: Annotated[ServiceLifecycle, Depends(get_lifecycle)]
) -> NotificationService:
    """Get notification service instance"""
    if not lc.notification_service:
        raise HTTPException(500, "NotificationService not initialised")
    return lc.notification_service