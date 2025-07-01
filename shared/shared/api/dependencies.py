
# -------------------------------
# shared/api/dependencies.py
# -------------------------------

"""
FastAPI dependencies for standardized API behavior.

This module provides reusable dependencies for pagination,
request tracking, and other common API patterns.
"""

from typing import Optional, Annotated
from fastapi import Query, Request, Depends
from pydantic import BaseModel, Field
import uuid


class PaginationParams(BaseModel):
    """Standard pagination parameters."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Items per page"
    )
    
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
        async def list_items(pagination: PaginationParams = Depends(get_pagination_params)):
            # Use pagination.offset and pagination.limit for DB query
            # Use pagination.page and pagination.limit for response
    """
    return PaginationParams(page=page, limit=limit)


def get_request_id(request: Request) -> str:
    """
    Get or generate request ID for the current request.
    
    This checks for existing request ID in:
    1. Request state (set by middleware)
    2. X-Request-ID header
    3. Generates new one if not found
    """
    # Check request state first
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    
    # Check headers
    request_id = request.headers.get("X-Request-ID")
    if request_id:
        return request_id
    
    # Generate new one
    return f"req_{uuid.uuid4().hex[:12]}"


# Type aliases for dependency injection
RequestIdDep = Annotated[str, Depends(get_request_id)]
PaginationDep = Annotated[PaginationParams, Depends(get_pagination_params)]


# Additional common dependencies

def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request headers."""
    return request.headers.get("User-Agent")


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Checks X-Forwarded-For header for proxied requests.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    return request.client.host if request.client else "unknown"


class RequestContext(BaseModel):
    """Complete request context for logging/auditing."""
    
    request_id: str
    trace_id: Optional[str] = None
    client_ip: str
    user_agent: Optional[str] = None
    method: str
    path: str
    
    @classmethod
    def from_request(cls, request: Request) -> "RequestContext":
        """Create context from FastAPI request."""
        return cls(
            request_id=get_request_id(request),
            trace_id=getattr(request.state, "trace_id", None),
            client_ip=get_client_ip(request),
            user_agent=get_user_agent(request),
            method=request.method,
            path=str(request.url.path)
        )


def get_request_context(request: Request) -> RequestContext:
    """FastAPI dependency to get full request context."""
    return RequestContext.from_request(request)


# Type alias for request context dependency
RequestContextDep = Annotated[RequestContext, Depends(get_request_context)]
