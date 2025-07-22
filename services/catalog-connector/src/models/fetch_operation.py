# src/models/fetch_operation.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from uuid import UUID, uuid4
from datetime import datetime
from shared.database.base import Base, TimestampedMixin

class FetchOperation(Base, TimestampedMixin):
    """High-level fetch operation tracking"""
    __tablename__ = "fetch_operations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # From sync request
    sync_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    shop_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sync_type: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Processing status
    status: Mapped[str] = mapped_column(String(20), default="started", index=True)
    
    # Options from request
    since_timestamp: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    force_reanalysis: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Progress tracking
    total_products_fetched: Mapped[int] = mapped_column(Integer, default=0)
    total_batches_published: Mapped[int] = mapped_column(Integer, default=0)
    
    # Associated bulk operation
    bulk_operation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    
    # Error tracking
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    __table_args__ = (
        Index("idx_fetch_operations_sync_shop", "sync_id", "shop_id"),
        Index("idx_fetch_operations_status", "status"),
    )
