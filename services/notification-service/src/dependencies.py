# services/notification-service/src/dependencies.py

"""
FastAPI dependency providers with type aliases for cleaner code.
"""
from typing import Annotated, Any
from fastapi import Depends, Request, HTTPException

from shared.api.dependencies import RequestIdDep, RequestContextDep, PaginationDep, CorrelationIdDep

from shared.messaging.jetstream_wrapper import JetStreamWrapper
from .lifecycle import ServiceLifecycle
from .services.notification_service import NotificationService
from .services.template_service import TemplateService
from .services.email_service import EmailService
from .events.publishers import NotificationEventPublisher

# ---------------------------------------------------------------- shared --- #
# Re-export shared dependencies for convenience
__all__ = [
    # Shared deps (re-exported)
    "RequestIdDep", 
    "RequestContextDep", 
    "PaginationDep", 
    "CorrelationIdDep",
    
    # Core deps
    "LifecycleDep",
    "ConfigDep",
    
    # Messaging deps
    "MessagingDep",
    "PublisherDep",
    
    # Service deps
    "NotificationServiceDep",
    "TemplateServiceDep",
    "EmailServiceDep",
]

# --------------------------- core singletons via lifecycle ----------------- #
def get_lifecycle(request: Request) -> ServiceLifecycle:
    return request.app.state.lifecycle                 

def get_config(request: Request):
    return request.app.state.config                   

# Type aliases for core dependencies
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[Any, Depends(get_config)]  # Replace Any with your Config type

# ------------------------------- messaging --------------------------------- #
def get_messaging_wrapper(lifecycle: LifecycleDep) -> JetStreamWrapper:
    if not lifecycle.messaging_wrapper:
        raise HTTPException(500, "Messaging not initialized")
    return lifecycle.messaging_wrapper

def get_publisher(wrapper: "MessagingDep") -> NotificationEventPublisher:
    pub = wrapper.get_publisher(NotificationEventPublisher)
    if not pub:
        raise HTTPException(500, "NotificationEventPublisher not initialized")
    return pub

# Type aliases for messaging
MessagingDep = Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)]
PublisherDep = Annotated[NotificationEventPublisher, Depends(get_publisher)]

# --------------------------------- utils ----------------------------------- #

def get_email_service(lifecycle: LifecycleDep) -> EmailService:
    if not lifecycle.email_service:
        raise HTTPException(500, "EmailService not initialized")
    return lifecycle.email_service


# Type aliases for utils
EmailServiceDep = Annotated[EmailService, Depends(get_email_service)]

# --------------------------- domain services ------------------------------- #
def get_template_service(lifecycle: LifecycleDep) -> TemplateService:
    if not lifecycle.template_service:
        raise HTTPException(500, "TemplateService not initialized")
    return lifecycle.template_service


def get_notification_service(lifecycle: LifecycleDep) -> NotificationService:
    if not lifecycle.notification_service:
        raise HTTPException(500, "NotificationService not initialized")
    return lifecycle.notification_service


# Type aliases for domain services
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
NotificationServiceDep = Annotated[NotificationService, Depends(get_notification_service)]
