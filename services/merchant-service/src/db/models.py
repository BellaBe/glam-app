# src/db/models.py
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SAEnum, Index, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from .session import Base


class MerchantStatus(StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    SUSPENDED = "SUSPENDED"
    UNINSTALLED = "UNINSTALLED"


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))

    platform_name: Mapped[str] = mapped_column(String, nullable=False)
    platform_shop_id: Mapped[str] = mapped_column(String, nullable=False)
    domain: Mapped[str] = mapped_column(String, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    primary_domain: Mapped[str | None] = mapped_column(String, nullable=True)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    platform_version: Mapped[str | None] = mapped_column(String, nullable=True)
    scopes: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[MerchantStatus] = mapped_column(
        SAEnum(MerchantStatus, name="merchantstatus"), nullable=False, default=MerchantStatus.PENDING, index=True
    )

    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    uninstalled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        Index("ix_merchants_platform_shop", "platform_name", "platform_shop_id", unique=True),
        Index("ix_merchants_platform_domain", "platform_name", "domain", unique=True),
        Index("ix_merchants_shop_domain", "platform_shop_id", "domain"),
        Index("ix_merchants_domain", "domain"),
    )


STATUS_TRANSITIONS = {
    MerchantStatus.PENDING: [
        MerchantStatus.ACTIVE,
        MerchantStatus.PAUSED,
        MerchantStatus.SUSPENDED,
        MerchantStatus.UNINSTALLED,
    ],
    MerchantStatus.ACTIVE: [MerchantStatus.PAUSED, MerchantStatus.SUSPENDED, MerchantStatus.UNINSTALLED],
    MerchantStatus.PAUSED: [MerchantStatus.ACTIVE, MerchantStatus.SUSPENDED, MerchantStatus.UNINSTALLED],
    MerchantStatus.SUSPENDED: [MerchantStatus.ACTIVE, MerchantStatus.PAUSED, MerchantStatus.UNINSTALLED],
    MerchantStatus.UNINSTALLED: [],
}
