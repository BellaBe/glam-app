# services/notification-service/src/schemas/common.py

"""Common schemas used across the notification service."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from enum import Enum
from uuid import UUID


class SortOrder(str, Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


class ShopInfo(BaseModel):
    """Shop identification information."""

    merchant_id: UUID
    merchant_domain: str = Field(..., min_length=1, max_length=255)
    shop_email: EmailStr
    unsubscribe_token: str = Field(..., min_length=1, max_length=255)
    dynamic_content: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Standard pagination parameters."""

    page: int = Field(1, ge=1)
    limit: int = Field(50, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class DateRangeFilter(BaseModel):
    """Date range filter for queries."""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def validate_range(self) -> "DateRangeFilter":
        """Validate that start is before end."""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date")
        return self
