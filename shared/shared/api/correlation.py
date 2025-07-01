
# -------------------------------
# shared/api/correlation.py
# -------------------------------

"""
Correlation ID support for distributed tracing across services.

This module provides utilities for managing correlation IDs that span
multiple services and requests in a distributed transaction.
"""

from typing import Optional, Annotated
from contextvars import ContextVar
from fastapi import Request, Depends
import uuid
import logging

logger = logging.getLogger(__name__)

# Context variable for storing correlation ID in async context
correlation_id_context: ContextVar[Optional[str]] = ContextVar(
    "correlation_id",
    default=None
)


def get_correlation_id(request: Request) -> str:
    """
    Get or generate correlation ID for the current request.
    
    This checks for existing correlation ID in:
    1. Request state (set by middleware)
    2. X-Correlation-ID header (from upstream service)
    3. Generates new one if not found (originating request)
    
    The correlation ID propagates through:
    - HTTP headers between services
    - Message bus events
    - Async context within a service
    """
    # Check request state first
    if hasattr(request.state, "correlation_id"):
        return request.state.correlation_id
    
    # Check headers (from upstream service)
    correlation_id = request.headers.get("X-Correlation-ID")
    if correlation_id:
        logger.debug(f"Using correlation ID from header: {correlation_id}")
        return correlation_id
    
    # Generate new one (this is the originating request)
    correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
    logger.info(f"Generated new correlation ID: {correlation_id}")
    return correlation_id


# Type alias for dependency injection
CorrelationIdDep = Annotated[str, Depends(get_correlation_id)]


def set_correlation_context(correlation_id: str) -> None:
    """Set correlation ID in async context."""
    correlation_id_context.set(correlation_id)


def get_correlation_context() -> Optional[str]:
    """Get correlation ID from async context."""
    return correlation_id_context.get()


class CorrelationContext:
    """
    Context manager for correlation ID propagation.
    
    Usage:
        async with CorrelationContext(correlation_id):
            # All async operations here will have access to correlation ID
            await some_async_function()
    """
    
    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self.token = None
    
    def __enter__(self):
        self.token = correlation_id_context.set(self.correlation_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            correlation_id_context.reset(self.token)
    
    async def __aenter__(self):
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)


# HTTP Client integration
def add_correlation_header(headers: dict) -> dict:
    """
    Add correlation ID to outgoing HTTP headers.
    
    Usage with httpx:
        async with httpx.AsyncClient() as client:
            headers = add_correlation_header({"Content-Type": "application/json"})
            response = await client.get(url, headers=headers)
    """
    correlation_id = get_correlation_context()
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    return headers


# NATS/Message Bus integration
def add_correlation_to_event(event_data: dict) -> dict:
    """
    Add correlation ID to event data for message bus.
    
    Usage:
        event_data = {
            "event_type": "SELFIE_UPLOADED",
            "data": {...}
        }
        event_with_correlation = add_correlation_to_event(event_data)
        await publisher.publish_event(event_with_correlation)
    """
    correlation_id = get_correlation_context()
    if correlation_id:
        if "metadata" not in event_data:
            event_data["metadata"] = {}
        event_data["metadata"]["correlation_id"] = correlation_id
    return event_data


def extract_correlation_from_event(event_data: dict) -> Optional[str]:
    """Extract correlation ID from event data."""
    return event_data.get("metadata", {}).get("correlation_id")


# Logging integration
class CorrelationLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically includes correlation ID.
    
    Usage:
        logger = CorrelationLoggerAdapter(logging.getLogger(__name__))
        logger.info("Processing request")  # Will include correlation_id in extra
    """
    
    def process(self, msg, kwargs):
        correlation_id = get_correlation_context()
        if correlation_id:
            if "extra" not in kwargs:
                kwargs["extra"] = {}
            kwargs["extra"]["correlation_id"] = correlation_id
        return msg, kwargs