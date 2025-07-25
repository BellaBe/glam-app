# File: shared/api/dependencies.py

"""
FastAPI dependencies for standardized API behavior.

Simplified to focus on commonly used dependencies.
"""

from typing import Annotated
from fastapi import Query, Request, Depends
from pydantic import BaseModel, Field
from .correlation import get_correlation_id


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=1000)
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.limit


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=1000, description="Items per page")
) -> PaginationParams:
    """
    FastAPI dependency for pagination parameters.
    
    Usage:
        @app.get("/items")
        async def list_items(pagination: PaginationDep):
            items = await db.query(offset=pagination.offset, limit=pagination.limit)
    """
    return PaginationParams(page=page, limit=limit)


def get_request_id(request: Request) -> str:
    """
    Get request ID from middleware-set state.
    
    Raises error if middleware hasn't run, ensuring proper initialization.
    """
    if not hasattr(request.state, "request_id"):
        raise RuntimeError(
            "Request ID not found. Ensure APIMiddleware is properly configured."
        )
    return request.state.request_id


# Type aliases for clean dependency injection
RequestIdDep = Annotated[str, Depends(get_request_id)]
PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]
CorrelationIdDep = Annotated[str, Depends(get_correlation_id)]  # Re-export for convenience


# Optional: Simplified request context for logging
class RequestContext(BaseModel):
    """Essential request context for logging/auditing."""
    
    request_id: str
    correlation_id: str
    method: str
    path: str
    
    @classmethod
    def from_request(cls, request: Request) -> "RequestContext":
        """Create context from FastAPI request."""
        return cls(
            request_id=get_request_id(request),
            correlation_id=get_correlation_id(request),
            method=request.method,
            path=str(request.url.path)
        )


def get_request_context(request: Request) -> RequestContext:
    """Get essential request context."""
    return RequestContext.from_request(request)


RequestContextDep = Annotated[RequestContext, Depends(get_request_context)]

def get_client_ip(request: Request) -> str:
    """
    Extract client IP address.
    Only add if needed for rate limiting or security.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


ClientIpDep = Annotated[str, Depends(get_client_ip)]