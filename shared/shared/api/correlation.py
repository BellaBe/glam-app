# File: shared/api/correlation.py

"""
Simplified correlation ID support for distributed tracing.

Focuses on the essential functionality needed for request tracing
across services without over-engineering.
"""

from typing import Optional, Annotated
from contextvars import ContextVar
from fastapi import Request, Depends
import uuid

# Context variable for async operations
_correlation_context: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)

def get_correlation_id(request: Request) -> str:
    """
    Get or generate correlation ID for the current request.

    Priority:
    1. Request state (set by middleware)
    2. X-Correlation-ID header (from upstream service)
    3. Generate new one (originating request)
    """
    # Check request state first
    if hasattr(request.state, "correlation_id"):
        return request.state.correlation_id

    # Check headers from upstream service
    correlation_id = request.headers.get("X-Correlation-ID")
    if correlation_id:
        return correlation_id

    # Generate new one
    return f"corr_{uuid.uuid4().hex[:12]}"


# FastAPI dependency
CorrelationIdDep = Annotated[str, Depends(get_correlation_id)]


def set_correlation_context(correlation_id: str) -> None:
    """Set correlation ID in async context."""
    _correlation_context.set(correlation_id)


def get_correlation_context() -> Optional[str]:
    """Get correlation ID from async context."""
    return _correlation_context.get()


# Essential integrations only


def add_correlation_header(headers: dict) -> dict:
    """
    Add correlation ID to outgoing HTTP headers.

    Usage:
        headers = add_correlation_header({"Content-Type": "application/json"})
        response = await client.get(url, headers=headers)
    """
    correlation_id = get_correlation_context()
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    return headers


def add_correlation_to_event(event_data: dict) -> dict:
    """
    Add correlation ID to message bus events.

    Usage:
        event_data = {"subject": "ORDER_CREATED", "data": {...}}
        event_with_correlation = add_correlation_to_event(event_data)
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
