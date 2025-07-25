# shared/messaging/event_context.py

from contextvars import ContextVar
from typing import Optional

# Context variables for correlation tracking
_correlation_context: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
_source_service_context: ContextVar[Optional[str]] = ContextVar('source_service', default=None)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from async context"""
    return _correlation_context.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in async context"""
    _correlation_context.set(correlation_id)


def get_source_service() -> Optional[str]:
    """Get current source service from async context"""
    return _source_service_context.get()


def set_source_service(source_service: str) -> None:
    """Set source service in async context"""
    _source_service_context.set(source_service)


def clear_context() -> None:
    """Clear all context variables"""
    _correlation_context.set(None)
    _source_service_context.set(None)