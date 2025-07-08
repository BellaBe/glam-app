# File: services/connector-service/src/schemas/catalog.py

"""Catalog data schemas."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class CatalogItemImage(BaseModel):
    """Catalog item image."""
    external_id: str
    url: str
    alt_text: Optional[str] = None
    position: int = 0


class CatalogItemVariant(BaseModel):
    """Catalog item variant."""
    external_id: str
    title: str
    sku: Optional[str] = None
    price: str
    inventory_quantity: int = 0
    options: Dict[str, str] = Field(default_factory=dict)


class CatalogItem(BaseModel):
    """Catalog item data."""
    external_id: str
    title: str
    description: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: str
    external_created_at: datetime
    external_updated_at: datetime
    variants: List[CatalogItemVariant] = Field(default_factory=list)
    images: List[CatalogItemImage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CatalogItemBatch(BaseModel):
    """Batch of catalog items."""
    page: int
    items: List[CatalogItem]
    has_more: bool = False
    cursor: Optional[str] = None


class CatalogDiffBatch(BaseModel):
    """Batch of catalog changes."""
    page: int
    items: List[CatalogItem]
    deleted_ids: List[str] = Field(default_factory=list)
    has_more: bool = False
    cursor: Optional[str] = None