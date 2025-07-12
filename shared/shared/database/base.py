
# glam-app/shared/database/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import DateTime, String
from datetime import datetime, timezone
from uuid import UUID


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models across microservices"""
    pass

class MerchantMixin:
    """Mixin to add merchant_id to any model"""
    merchant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), 
        nullable=False, 
        index=True
    )
    merchant_domain: Mapped[str] = mapped_column(
        String(255), 
        nullable=False, 
        index=True
    )


class TimestampedMixin:
    """Mixin to add created_at and updated_at to any model"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality"""
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)