# services/catalog-service/src/schemas/catalog.py
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# Input DTOs
class CatalogItemCreate(BaseModel):
    """DTO for creating/updating catalog item"""

    merchant_id: str
    platform_name: str
    platform_id: str
    platform_domain: str
    product_id: str
    variant_id: str
    image_id: str | None = None
    product_title: str
    variant_title: str
    sku: str | None = None
    price: Decimal
    currency: str = "USD"
    inventory_quantity: int = 0
    image_url: str | None = None
    platform_created_at: datetime | None = None
    platform_updated_at: datetime | None = None
    synced_at: datetime

    model_config = ConfigDict(extra="forbid")


class CatalogItemUpdate(BaseModel):
    """DTO for partial catalog item update"""

    price: Decimal | None = None
    inventory_quantity: int | None = None
    sync_status: str | None = None
    analysis_status: str | None = None

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
    image_id: str | None
    product_title: str
    variant_title: str
    sku: str | None
    price: Decimal
    currency: str
    inventory_quantity: int
    image_url: str | None
    sync_status: str
    analysis_status: str
    synced_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
