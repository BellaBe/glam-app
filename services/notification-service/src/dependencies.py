# File: services/notification-service/src/dependencies.py
"""
Notification service dependencies for FastAPI application.
This module provides FastAPI dependencies for the notification service,
including lifecycle management, messaging, email, notification, template,
and preference services.
"""
from typing import Annotated
from fastapi import Depends, Request
from shared.api.dependencies import RequestIdDep, RequestContextDep, PaginationDep
from shared.api.correlation import CorrelationIdDep, get_correlation_context
from shared.messaging.jetstream_wrapper import JetStreamWrapper
from .services.notification_service import NotificationService
from .services.template_service import TemplateService
from .services.email_service import EmailService
from .services.preference_service import PreferenceService
from .events.publishers import NotificationPublisher
from .utils.template_engine import TemplateEngine
from .utils.rate_limiter import RateLimiter
from .lifecycle import ServiceLifecycle
from shared.utils.logger import create_logger

# Re-export shared dependencies for convenience
__all__ = [
    'RequestIdDep',
    'RequestContextDep', 
    'PaginationDep',
    'CorrelationIdDep',
    'get_lifecycle',
    'get_messaging_wrapper',
    'get_publisher',
    'get_template_engine',
    'get_rate_limiter',
    'get_email_service',
    'get_notification_service',
    'get_template_service',
    'get_preference_service'
]

def get_lifecycle(request: Request) -> ServiceLifecycle:
    """Get service lifecycle from app state"""
    return request.app.state.lifecycle

def get_messaging_wrapper(
    lifecycle: Annotated[ServiceLifecycle, Depends(get_lifecycle)]
) -> JetStreamWrapper:
    """Get messaging wrapper from lifecycle"""
    if not lifecycle.messaging_wrapper:
        raise RuntimeError("Messaging not initialized")
    return lifecycle.messaging_wrapper

def get_publisher(
    wrapper: Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)]
) -> NotificationPublisher:
    """Get notification publisher"""
    return wrapper.publishers[NotificationPublisher.__name__]

def get_template_engine() -> TemplateEngine:
    """Get template engine instance"""
    return TemplateEngine()

def get_rate_limiter(request: Request) -> RateLimiter:
    """Get rate limiter instance"""
    config = request.app.state.config
    return RateLimiter(config.rate_limit_config.dict())

def get_email_service(request: Request) -> EmailService:
    """Get email service instance"""
    config = request.app.state.config
    logger = create_logger("email-service")
    
    email_config = {
        'primary_provider': config.PRIMARY_PROVIDER,
        'fallback_provider': config.FALLBACK_PROVIDER,
        'sendgrid_config': config.sendgrid_config.dict(),
        'ses_config': config.ses_config.dict(),
        'smtp_config': config.smtp_config.dict()
    }
    
    return EmailService(email_config, logger)

def get_notification_service(
    publisher: Annotated[NotificationPublisher, Depends(get_publisher)],
    email_service: Annotated[EmailService, Depends(get_email_service)],
    template_engine: Annotated[TemplateEngine, Depends(get_template_engine)],
    rate_limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
    request: Request
) -> NotificationService:
    """Get notification service with dependencies"""
    logger = create_logger("notification-service")
    return NotificationService(
        publisher, email_service, template_engine, rate_limiter, logger
    )

def get_template_service(
    template_engine: Annotated[TemplateEngine, Depends(get_template_engine)],
    request: Request
) -> TemplateService:
    """Get template service"""
    logger = create_logger("template-service")
    return TemplateService(template_engine, logger)

def get_preference_service(request: Request) -> PreferenceService:
    """Get preference service"""
    logger = create_logger("preference-service")
    return PreferenceService(logger)