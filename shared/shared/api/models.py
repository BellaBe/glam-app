# -------------------------------
# shared/api/models.py
# -------------------------------

"""
Unified API response models for glam-app services.
Consolidates all response structures into a single, consistent pattern.
"""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar
from urllib.parse import urlencode

from pydantic import BaseModel, ConfigDict, Field

# Generic type for response data
T = TypeVar("T")


class Meta(BaseModel):
    """Metadata included in all responses."""

    correlation_id: str | None = Field(None, description="Distributed tracing ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Response timestamp in UTC")

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class Pagination(BaseModel):
    """Pagination metadata for list responses."""

    page: int = Field(ge=1)
    limit: int = Field(ge=1, le=1000)
    total: int = Field(ge=0)
    pages: int = Field(ge=0)
    has_next: bool
    has_previous: bool

    @classmethod
    def create(cls, page: int, limit: int, total: int) -> "Pagination":
        """Create pagination from parameters."""
        pages = (total + limit - 1) // limit if total > 0 else 0
        return cls(page=page, limit=limit, total=total, pages=pages, has_next=page < pages, has_previous=page > 1)


class Links(BaseModel):
    self: str
    next: str | None = None
    previous: str | None = None
    first: str | None = None
    last: str | None = None

    @classmethod
    def create_paginated(cls, base_path: str, page: int, limit: int, pages: int, **query_params) -> "Links":
        """Create relative (path + query) pagination links with URL encoding.
        Strips reserved pagination keys if present in query_params.
        """
        # strip reserved keys that we pass explicitly
        qp = {k: v for k, v in query_params.items() if k not in {"page", "limit"} and v is not None}

        def build_url(page_num: int) -> str:
            params = {**qp, "page": page_num, "limit": limit}
            return f"{base_path}?{urlencode(params, doseq=True)}"

        return cls(
            self=build_url(page),
            next=build_url(page + 1) if page < pages else None,
            previous=build_url(page - 1) if page > 1 else None,
            first=build_url(1) if pages > 0 else None,
            last=build_url(pages) if pages > 0 else None,
        )


class ErrorDetail(BaseModel):
    """Error information."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ApiResponse(BaseModel, Generic[T]):
    """
    Unified API response structure.
    Used for both success and error responses.
    """

    # For success responses
    data: T | None = None

    # For error responses
    error: ErrorDetail | None = None

    # Always present
    meta: Meta

    # Optional for paginated responses
    pagination: Pagination | None = None
    links: Links | None = None

    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
