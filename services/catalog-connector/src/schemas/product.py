# src/schemas/product.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ProductVariantOut(BaseModel):
    """Transformed product variant for catalog service"""
    product_id: str
    variant_id: str
    image_id: Optional[str] = None
    
    # Product-level data
    title: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Variant-level data
    variant_title: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    inventory_quantity: int = 0
    variant_options: Dict[str, Any] = Field(default_factory=dict)
    
    # Image
    image_url: Optional[str] = None
    
    # Shopify timestamps
    shopify_created_at: Optional[datetime] = None
    shopify_updated_at: Optional[datetime] = None

class ProductsBatchOut(BaseModel):
    """Batch of products to send to catalog service"""
    event_id: str
    sync_id: UUID
    shop_id: str
    bulk_operation_id: str
    batch_number: int
    total_batches: int
    products: List[ProductVariantOut]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
