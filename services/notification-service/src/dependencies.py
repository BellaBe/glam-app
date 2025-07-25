"""
FastAPI dependency providers with type aliases for cleaner code.
"""
from typing import Annotated, Any

from fastapi import Depends, Request, HTTPException
from shared.api.dependencies import (
    RequestIdDep, RequestContextDep, PaginationDep, CorrelationIdDep,
)

from shared.messaging.jetstream_client import JetStreamClient
from .lifecycle import ServiceLifecycle
from .services.notification_service import NotificationService
from .services.template_service import TemplateService
from .services.email_service import EmailService
from .events.publishers import EmailSendPublisher

# ---------------------------------------------------------------- exports ---
__all__ = [
    # shared deps
    "RequestIdDep", "RequestContextDep", "PaginationDep", "CorrelationIdDep",
    # core
    "LifecycleDep", "ConfigDep",
    # messaging
    "MessagingClientDep", "SendEmailPublisherDep",
    # services
    "NotificationServiceDep", "TemplateServiceDep", "EmailServiceDep",
]

# ---------------------------------------------------------------- core -------
def _lifecycle(req: Request) -> ServiceLifecycle:
    return req.app.state.lifecycle

def _config(req: Request):
    return req.app.state.config

LifecycleDep = Annotated[ServiceLifecycle, Depends(_lifecycle)]
ConfigDep    = Annotated[Any,             Depends(_config)]

# ---------------------------------------------------------------- messaging --
def _messaging_client(lc: LifecycleDep) -> JetStreamClient:
    if not lc.messaging_client:
        raise HTTPException(500, "Messaging client not initialised")
    return lc.messaging_client

def _publisher(lc: LifecycleDep) -> EmailSendPublisher:
    if not lc.email_send_publisher:
        raise HTTPException(500, "EmailSendPublisher not initialised")
    return lc.email_send_publisher

MessagingClientDep   = Annotated[JetStreamClient,    Depends(_messaging_client)]
SendEmailPublisherDep = Annotated[EmailSendPublisher, Depends(_publisher)]

# ---------------------------------------------------------------- utilities --
def _email_service(lc: LifecycleDep) -> EmailService:
    if not lc.email_service:
        raise HTTPException(500, "EmailService not initialised")
    return lc.email_service

EmailServiceDep = Annotated[EmailService, Depends(_email_service)]

# ----------------------------------------------------------- domain services -
def _template_service(lc: LifecycleDep) -> TemplateService:
    if not lc.template_service:
        raise HTTPException(500, "TemplateService not initialised")
    return lc.template_service

def _notification_service(lc: LifecycleDep) -> NotificationService:
    if not lc.notification_service:
        raise HTTPException(500, "NotificationService not initialised")
    return lc.notification_service

TemplateServiceDep     = Annotated[TemplateService,     Depends(_template_service)]
NotificationServiceDep = Annotated[NotificationService, Depends(_notification_service)]
