# File: services/connector-service/src/schemas/commands.py

"""Command schemas for event processing."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class FetchItemsCommand(BaseModel):
    """Command to fetch catalog items."""
    store_id: str = Field(..., description="Store identifier")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(250, ge=1, le=250, description="Items per page")
    cursor: Optional[str] = Field(None, description="Pagination cursor")
    fields: Optional[List[str]] = Field(None, description="Fields to include")


class FetchItemsDiffCommand(BaseModel):
    """Command to fetch changed catalog items."""
    store_id: str = Field(..., description="Store identifier")
    since: datetime = Field(..., description="Fetch changes since this time")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(250, ge=1, le=250, description="Items per page")
    cursor: Optional[str] = Field(None, description="Pagination cursor")


class ValidateStoreCommand(BaseModel):
    """Command to validate store connectivity."""
    store_id: str = Field(..., description="Store identifier")
