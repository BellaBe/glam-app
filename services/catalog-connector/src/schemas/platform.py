# services/platform-connector/src/schemas/platform.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PlatformProduct(BaseModel):
    """Internal platform product format"""

    platform_name: str
    platform_shop_id: str
    domain: str
    product_id: str
    variant_id: str
    product_title: str
    variant_title: str
    sku: str | None
    price: float
    currency: str
    inventory: int
    image_url: str | None
    created_at: datetime | None
    updated_at: datetime | None


class ProductBatch(BaseModel):
    """Batch of products from platform"""

    merchant_id: str
    sync_id: str
    platform_name: str
    platform_shop_id: str
    domain: str
    products: list[dict[str, Any]]
    batch_num: int
    has_more: bool
