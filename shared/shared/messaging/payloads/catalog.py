# shared/messaging/payloads/catalog.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from enum import Enum


class SyncType(str, Enum):
    FULL="full"
    INCREMENTAL="incremental"
    
    
class SyncRequestedPayload(BaseModel):
    """Request to sync catalog"""
    merchant_id: UUID
    sync_type: SyncType
    requested_by: str
    platform: str = Field(default="shopify")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ProductsStoredPayload(BaseModel):
    """Products stored in catalog"""
    merchant_id: UUID
    sync_id: UUID
    products_stored: int = Field(..., ge=0)
    products_updated: int = Field(..., ge=0)
    storage_duration_seconds: float = Field(..., ge=0)
    platform: str


class SyncCompletedPayload(BaseModel):
    """Catalog sync completed"""
    merchant_id: UUID
    sync_id: UUID
    total_products: int = Field(..., ge=0)
    sync_duration_seconds: float = Field(..., ge=0)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))