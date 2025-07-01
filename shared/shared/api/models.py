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
    meta: Optional[ResponseMeta] = Field(None, description="Response metadata")
    
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    
    @classmethod
    def from_exception(
        cls,
        exc: Any,
        *,
        request_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        include_details: bool = True
    ) -> tuple["ErrorResponse", int]:
        """
        Create an ErrorResponse from any exception.
        
        Args:
            exc: The exception to convert
            request_id: Request ID for tracing
            correlation_id: Correlation ID for distributed tracing
            include_details: Whether to include detailed error information
            
        Returns:
            Tuple of (ErrorResponse, status_code)
        """
        from ..errors.base import GlamBaseError
        
        error_dict: Dict[str, Any] = {}
        status = 500
        
        if isinstance(exc, GlamBaseError):
            # Our custom errors - use their structure
            error_dict = exc.to_dict()
            status = exc.status
        elif isinstance(exc, dict):
            # Error dict provided
            error_dict = exc
            # Extract status if provided
            status = error_dict.pop("status", 500)
        else:
            # Unexpected error - sanitize for production
            error_dict = {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
            status = 500
            
            # Log the full traceback for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(
                "Unhandled exception",
                extra={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "request_id": request_id,
                    "correlation_id": correlation_id
                }
            )
        
        # Remove details in production if requested
        if not include_details and "details" in error_dict:
            error_dict.pop("details", None)
        
        error_detail = ErrorDetail(**error_dict)
        
        # Create meta only if we have request_id or correlation_id
        meta = None
        if request_id or correlation_id:
            meta = ResponseMeta(
                request_id=request_id or f"req_{uuid.uuid4().hex[:12]}",
                correlation_id=correlation_id
            )
        
        return cls(
            error=error_detail,
            meta=meta
        ), status
