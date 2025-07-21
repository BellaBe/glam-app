
# glam-app/shared/database/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import DateTime, String, func, Index, MetaData
from datetime import datetime
from uuid import UUID


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True            # <- prevents accidental table mapping

    # optional: naming convention for Alembic
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

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
    __table_args__ = (
    Index("idx_merchant_id_domain", "merchant_id", "merchant_domain"),)


class TimestampedMixin:
    """Mixin to add created_at and updated_at to any model"""
    created_at = mapped_column( DateTime(timezone=True), server_default=func.now(), nullable=False, index=True )
    updated_at = mapped_column( DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False )


class SoftDeleteMixin:
    """Mixin to add soft delete functionality"""
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)