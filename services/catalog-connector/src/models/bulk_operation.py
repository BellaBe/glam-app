# src/models/bulk_operation.py
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Boolean, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base, TimestampedMixin


class BulkOperationStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class BulkOperation(Base, TimestampedMixin):
    """Shopify bulk operation tracking"""

    __tablename__ = "bulk_operations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Associated sync operation
    sync_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    shop_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Shopify bulk operation details
    shopify_bulk_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default=BulkOperationStatus.CREATED, index=True)

    # GraphQL query used
    graphql_query: Mapped[str] = mapped_column(Text, nullable=False)

    # Results
    object_count: Mapped[int] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)
    download_url: Mapped[str] = mapped_column(Text, nullable=True)
    partial_data_url: Mapped[str] = mapped_column(Text, nullable=True)

    # Error information
    error_code: Mapped[str] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    # Processing tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)

    # Webhook tracking
    webhook_received: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_received_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)

    __table_args__ = (
        Index("idx_bulk_operations_sync_shop", "sync_id", "shop_id"),
        Index("idx_bulk_operations_status", "status"),
    )
