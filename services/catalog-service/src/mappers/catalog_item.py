# src/mappers/item_mapper.py
from shared.mappers.crud import CRUDMapper
from ..models.item import Item
from ..schemas.item import ItemOut
from typing import Optional
from pydantic import BaseModel

class ItemIn(BaseModel):
    """Input DTO for creating items"""
    shop_id: str
    product_id: str
    variant_id: str
    image_id: Optional[str] = None
    product_title: Optional[str] = None
    product_description: Optional[str] = None
    product_vendor: Optional[str] = None
    product_type: Optional[str] = None
    product_tags: Optional[list[str]] = None
    variant_title: Optional[str] = None
    variant_sku: Optional[str] = None
    variant_price: Optional[float] = None
    variant_inventory: int = 0
    variant_options: Optional[str] = None
    image_url: Optional[str] = None
    gender: str = "unisex"
    shopify_created_at: Optional[datetime] = None
    shopify_updated_at: Optional[datetime] = None

class ItemPatch(BaseModel):
    """Patch DTO for updating items"""
    sync_status: Optional[str] = None
    analysis_status: Optional[str] = None
    cached_image_path: Optional[str] = None
    synced_at: Optional[datetime] = None
    requeued_at: Optional[datetime] = None

class ItemMapper(CRUDMapper[Item, ItemIn, ItemPatch, ItemOut]):
    """CRUD mapper for Item"""
    model_cls = Item
    out_schema = ItemOut