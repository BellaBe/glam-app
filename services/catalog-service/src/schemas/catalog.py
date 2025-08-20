# services/catalog-service/src/schemas/catalog.py
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# Input DTOs
class CatalogItemCreate(BaseModel):
    """DTO for creating/updating catalog item"""
    merchant_id: str
    platform_name: str
    platform_id: str
    platform_domain: str
    product_id: str
    variant_id: str
    image_id: Optional[str] = None
    product_title: str
    variant_title: str
    sku: Optional[str] = None
    price: Decimal
    currency: str = "USD"
    inventory_quantity: int = 0
    image_url: Optional[str] = None
    platform_created_at: Optional[datetime] = None
    platform_updated_at: Optional[datetime] = None
    synced_at: datetime
    
    model_config = ConfigDict(extra="forbid")

class CatalogItemUpdate(BaseModel):
    """DTO for partial catalog item update"""
    price: Optional[Decimal] = None
    inventory_quantity: Optional[int] = None
    sync_status: Optional[str] = None
    analysis_status: Optional[str] = None
    
    model_config = ConfigDict(extra="forbid")

# Output DTOs
class CatalogItemOut(BaseModel):
    """DTO for catalog item response"""
    id: str
    merchant_id: str
    platform_name: str
    platform_id: str
    platform_domain: str
    product_id: str
    variant_id: str
    image_id: Optional[str]
    product_title: str
    variant_title: str
    sku: Optional[str]
    price: Decimal
    currency: str
    inventory_quantity: int
    image_url: Optional[str]
    sync_status: str
    analysis_status: str
    synced_at: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)