# services/catalog-service/src/models/sync_operation.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from uuid import UUID, uuid4
from datetime import datetime
from shared.database.base import Base, TimestampedMixin

class SyncOperation(Base, TimestampedMixin):
    """Sync operation tracking with retry logic"""
    __tablename__ = "sync_operations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    shop_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Sync configuration
    sync_type: Mapped[str] = mapped_column(String(20), default="full")
    status: Mapped[str] = mapped_column(String(20), default="running", index=True)
    
    # Progress tracking
    total_products: Mapped[int] = mapped_column(Integer, default=0)
    processed_products: Mapped[int] = mapped_column(Integer, default=0)
    failed_products: Mapped[int] = mapped_column(Integer, default=0)
    images_cached: Mapped[int] = mapped_column(Integer, default=0)
    analysis_requested: Mapped[int] = mapped_column(Integer, default=0)
    analysis_completed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Shopify bulk operation tracking
    bulk_operation_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    bulk_retry_count: Mapped[int] = mapped_column(Integer, default=0)
    shopify_webhook_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    
    # Incremental sync support
    since_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    
    # Timing and status
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    __table_args__ = (
        Index("idx_sync_shop_status", "shop_id", "status"),
    )