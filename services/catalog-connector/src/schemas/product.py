# src/schemas/product.py
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProductVariantOut(BaseModel):
    """Transformed product variant for catalog service"""

    product_id: str
    variant_id: str
    image_id: str | None = None

    # Product-level data
    title: str | None = None
    description: str | None = None
    vendor: str | None = None
    product_type: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Variant-level data
    variant_title: str | None = None
    sku: str | None = None
    price: float | None = None
    inventory_quantity: int = 0
    variant_options: dict[str, Any] = Field(default_factory=dict)

    # Image
    image_url: str | None = None

    # Shopify timestamps
    shopify_created_at: datetime | None = None
    shopify_updated_at: datetime | None = None


class ProductsBatchOut(BaseModel):
    """Batch of products to send to catalog service"""

    event_id: str
    sync_id: UUID
    shop_id: str
    bulk_operation_id: str
    batch_number: int
    total_batches: int
    products: list[ProductVariantOut]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
