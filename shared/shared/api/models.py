# -------------------------------
# shared/api/models.py
# -------------------------------

"""
Standardized API response models for glam-app services.

These models ensure consistent response structure across all microservices.
"""

from typing import TypeVar, Generic, Optional, Any, Dict, List, Union
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
import uuid

# Generic type for response data
DataT = TypeVar("DataT")


class ResponseMeta(BaseModel):
    """Metadata included in all responses."""
    
    request_id: str = Field(
        description="Unique request identifier for tracing"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response timestamp in UTC"
    )
    correlation_id: Optional[str] = Field(
        None,
        description="Correlation ID for distributed tracing across services"
    )
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class Links(BaseModel):
    """HATEOAS links for resource navigation."""
    
    self: str = Field(description="Link to current resource")
    next: Optional[str] = Field(None, description="Link to next page")
    previous: Optional[str] = Field(None, description="Link to previous page")
    first: Optional[str] = Field(None, description="Link to first page")
    last: Optional[str] = Field(None, description="Link to last page")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    
    page: int = Field(ge=1, description="Current page number")
    limit: int = Field(ge=1, le=1000, description="Items per page")
    total: int = Field(ge=0, description="Total number of items")
    pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether next page exists")
    has_previous: bool = Field(description="Whether previous page exists")
    
    @classmethod
    def from_params(
        cls,
        page: int,
        limit: int,
        total: int
    ) -> "PaginationMeta":
        """Create pagination metadata from parameters."""
        pages = (total + limit - 1) // limit if total > 0 else 0
        
        return cls(
            page=page,
            limit=limit,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_previous=page > 1
        )


class SuccessResponse(BaseModel, Generic[DataT]):
    """
    Standard success response format.
    
    This is the standard format for all successful API responses
    across glam-app services.
    """
    
    data: DataT = Field(description="Response data")
    meta: ResponseMeta = Field(description="Response metadata")
    pagination: Optional[PaginationMeta] = Field(
        None,
        description="Pagination info for list endpoints"
    )
    links: Optional[Links] = Field(
        None,
        description="HATEOAS links for resource navigation"
    )
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    code: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error context"
    )


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    
    This matches the error structure from the error handling layer
    and provides a consistent error format across services.
    """
    
    error: ErrorDetail = Field(description="Error information")
    meta: ResponseMeta = Field(description="Response metadata")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    @classmethod
    def from_error(
        cls,
        error: Any,
        request_id: str,
        correlation_id: Optional[str] = None
    ) -> "ErrorResponse":
        """Create ErrorResponse from an exception or error dict."""
        if hasattr(error, "to_dict"):
            # It's a GlamBaseError
            error_dict = error.to_dict()
            error_detail = ErrorDetail(**error_dict)
        elif isinstance(error, dict):
            # Already a dict
            error_detail = ErrorDetail(**error)
        else:
            # Generic error
            error_detail = ErrorDetail(
                code="INTERNAL_ERROR",
                message=str(error),
                details=None
            )
        
        return cls(
            error=error_detail,
            meta=ResponseMeta(
                request_id=request_id,
                correlation_id=correlation_id
            )
        )


# Response builder functions

def success_response(
    data: DataT,
    *,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    links: Optional[Links] = None,
    extra_meta: Optional[Dict[str, Any]] = None
) -> SuccessResponse[DataT]:
    """
    Create a standard success response.
    
    Args:
        data: The response data
        request_id: Request ID for tracing
        correlation_id: Correlation ID for distributed tracing
        links: Optional HATEOAS links
        extra_meta: Additional metadata to include
        
    Returns:
        SuccessResponse instance
    """
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    meta = ResponseMeta(
        request_id=request_id,
        correlation_id=correlation_id
    )
    
    # Add any extra metadata
    if extra_meta:
        meta_dict = meta.model_dump()
        meta_dict.update(extra_meta)
        meta = ResponseMeta(**meta_dict)
    
    return SuccessResponse(
        data=data,
        meta=meta,
        pagination=None,  # Explicitly set to None
        links=links
    )


def error_response(
    code: str,
    message: str,
    *,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    status_code: int = 500
) -> tuple[ErrorResponse, int]:
    """
    Create a standard error response.
    
    Args:
        code: Error code
        message: Human-readable error message
        details: Additional error context
        request_id: Request ID for tracing
        correlation_id: Correlation ID for distributed tracing
        status_code: HTTP status code
        
    Returns:
        Tuple of (ErrorResponse, status_code)
    """
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    error_detail = ErrorDetail(
        code=code,
        message=message,
        details=details
    )
    
    response = ErrorResponse(
        error=error_detail,
        meta=ResponseMeta(
            request_id=request_id,
            correlation_id=correlation_id
        )
    )
    
    return response, status_code


def paginated_response(
    data: List[DataT],
    *,
    page: int,
    limit: int,
    total: int,
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    base_url: str,
    **query_params
) -> SuccessResponse[List[DataT]]:
    """
    Create a paginated success response.
    
    Args:
        data: List of items for current page
        page: Current page number
        limit: Items per page
        total: Total number of items
        request_id: Request ID for tracing
        correlation_id: Correlation ID for distributed tracing
        base_url: Base URL for pagination links
        **query_params: Additional query parameters to preserve
        
    Returns:
        SuccessResponse with pagination
    """
    if request_id is None:
        request_id = f"req_{uuid.uuid4().hex[:12]}"
    
    # Create pagination metadata
    pagination = PaginationMeta.from_params(page, limit, total)
    
    # Build pagination links
    def build_url(page_num: int) -> str:
        params = {**query_params, "page": page_num, "limit": limit}
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query}"
    
    links = Links(
        self=build_url(page),
        next=build_url(page + 1) if pagination.has_next else None,
        previous=build_url(page - 1) if pagination.has_previous else None,
        first=build_url(1) if pagination.pages > 0 else None,
        last=build_url(pagination.pages) if pagination.pages > 0 else None
    )
    
    return SuccessResponse(
        data=data,
        meta=ResponseMeta(
            request_id=request_id,
            correlation_id=correlation_id
        ),
        pagination=pagination,
        links=links
    )
