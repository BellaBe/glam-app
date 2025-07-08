# File: services/connector-service/src/schemas/store.py

"""Store connection schemas."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, SecretStr

from ..models.store_connection import StoreStatus


class StoreConnectionCreate(BaseModel):
    """Create a new store connection."""
    store_id: str = Field(..., min_length=1, max_length=50)
    shopify_domain: str = Field(..., min_length=1, max_length=255)
    access_token: SecretStr = Field(..., min_length=1)
    api_version: str = Field("2024-01", pattern="^\\d{4}-\\d{2}$")
    webhook_secret: Optional[SecretStr] = None


class StoreConnectionUpdate(BaseModel):
    """Update store connection."""
    access_token: Optional[SecretStr] = None
    api_version: Optional[str] = Field(None, pattern="^\\d{4}-\\d{2}$")
    webhook_secret: Optional[SecretStr] = None
    status: Optional[StoreStatus] = None


class StoreConnectionResponse(BaseModel):
    """Store connection response."""
    id: UUID
    store_id: str
    shopify_domain: str
    api_version: str
    status: StoreStatus
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
