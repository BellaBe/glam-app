# services/platform-connector/src/schemas/platform.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class PlatformProduct(BaseModel):
    """Internal platform product format"""
    platform_name: str
    platform_id: str
    platform_domain: str
    product_id: str
    variant_id: str
    product_title: str
    variant_title: str
    sku: Optional[str]
    price: float
    currency: str
    inventory: int
    image_url: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

class ProductBatch(BaseModel):
    """Batch of products from platform"""
    merchant_id: str
    sync_id: str
    platform_name: str
    platform_id: str
    platform_domain: str
    products: List[Dict[str, Any]]
    batch_num: int
    has_more: bool