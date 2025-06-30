
# glam-app/shared/database/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime, timezone


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all database models across microservices"""
    pass


class TimestampedMixin:
    """Mixin to add created_at and updated_at to any model"""
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality"""
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)