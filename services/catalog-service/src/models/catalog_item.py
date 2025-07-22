# services/catalog-service/src/models/item.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, Text, DECIMAL, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from uuid import UUID, uuid4
from datetime import datetime
from shared.database.base import Base, TimestampedMixin

class CatalogItem(Base, TimestampedMixin):
    """Product variant model with multi-tenancy"""
    __tablename__ = "items"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Multi-tenant isolation
    shop_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Shopify IDs
    product_id: Mapped[str] = mapped_column(String(100), nullable=False) # Platform product ID
    variant_id: Mapped[str] = mapped_column(String(100), nullable=False)
    image_id: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Product-level data (cached for performance)
    product_title: Mapped[str] = mapped_column(String(500), nullable=True)
    product_description: Mapped[str] = mapped_column(Text, nullable=True)
    product_vendor: Mapped[str] = mapped_column(String(255), nullable=True)
    product_type: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    product_tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    
    # Variant-specific data
    variant_title: Mapped[str] = mapped_column(String(500), nullable=True)
    variant_sku: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    variant_price: Mapped[float] = mapped_column(DECIMAL(10,2), nullable=True)
    variant_inventory: Mapped[int] = mapped_column(Integer, default=0)
    variant_options: Mapped[dict] = mapped_column(Text, nullable=True)  # JSON as text
    
    # Image and caching
    image_url: Mapped[str] = mapped_column(Text, nullable=True)
    cached_image_path: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Processing status
    sync_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    
    # Metadata
    gender: Mapped[str] = mapped_column(String(10), default="unisex")
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    shopify_created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    shopify_updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    requeued_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    
    __table_args__ = (
        Index("idx_items_unique_variant", "shop_id", "product_id", "variant_id", unique=True),
        Index("idx_items_sync_status", "shop_id", "sync_status"),
        Index("idx_items_analysis_status", "shop_id", "analysis_status"),
        Index("idx_items_product_id", "shop_id", "product_id"),
        Index("idx_items_pending_analysis", "shop_id", "synced_at", 
              postgresql_where="analysis_status = 'pending'"),
    )