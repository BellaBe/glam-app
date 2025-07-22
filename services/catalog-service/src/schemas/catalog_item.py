# src/schemas/item.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class ItemOut(BaseModel):
    """Output DTO for catalog item"""
    id: UUID
    shop_id: str
    product_id: str
    variant_id: str
    
    # Product data
    product_title: Optional[str]
    product_description: Optional[str]
    product_vendor: Optional[str]
    product_type: Optional[str]
    product_tags: Optional[List[str]]
    
    # Variant data
    variant_title: Optional[str]
    variant_sku: Optional[str]
    variant_price: Optional[float]
    variant_inventory: int
    variant_options: Optional[str]  # JSON string
    
    # Image and status
    image_url: Optional[str]
    cached_image_path: Optional[str]
    sync_status: str
    analysis_status: str
    
    # Metadata
    gender: str
    published: bool
    shopify_created_at: Optional[datetime]
    shopify_updated_at: Optional[datetime]
    synced_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ItemWithAnalysisOut(ItemOut):
    """Item with analysis results"""
    analysis: Optional[Dict[str, Any]] = None

class ProductSearchParams(BaseModel):
    """Search parameters for products"""
    shop_id: str = Field(..., min_length=1)
    category: Optional[str] = None
    status: Optional[str] = None
    search: Optional[str] = None
    limit: int = Field(50, ge=1, le=250)
    offset: int = Field(0, ge=0)