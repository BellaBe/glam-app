# shared/events/__init__.py
"""
Shared event handling module for glam-app microservices.

This module provides:
- Event type definitions and stream mapping
- Base publisher/subscriber classes
- Event context management
- Stream configuration
"""

from .base import (
    Streams,
    EventWrapper,
    # EventDefinition removed
)

from .context import (
    EventContext,
    EventPayload,
    EventContextManager,
)

from .base_publisher import DomainEventPublisher
from .base_subscriber import DomainEventSubscriber

from .mappers import (
    # EVENT_REGISTRY removed
    SERVICE_STREAM_MAP,
    get_stream_subjects,
    get_stream_for_service,
    get_stream_from_event_type,
)

__all__ = [
    # Base types
    "Streams",
    "EventWrapper",
    
    # Context management
    "EventContext",
    "EventPayload", 
    "EventContextManager",
    
    # Publishers/Subscribers
    "DomainEventPublisher",
    "DomainEventSubscriber",
    
    # Mappers
    "SERVICE_STREAM_MAP",
    "get_stream_subjects",
    "get_stream_for_service",
    "get_stream_from_event_type",
]