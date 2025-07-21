from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from ..shared.database.base import Base, TimestampedMixin
from .enums import MerchantStatusEnum


class Merchant(Base, TimestampedMixin):
    __tablename__ = "merchants"

    # ---------------- Primary ---------------- #
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # ---------------- Shopify Integration ---------------- #
    shop_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    shop_domain: Mapped[str] = mapped_column(String(255), index=True)
    shop_name: Mapped[str] = mapped_column(String(255))
    shop_url: Mapped[str | None] = mapped_column(String(255))
    shopify_access_token: Mapped[str] = mapped_column(String)
    platform_api_version: Mapped[str] = mapped_column(String(32), default="2024-01")

    # ---------------- Business Identity ---------------- #
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(32))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    country: Mapped[str | None] = mapped_column(String(2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    language: Mapped[str] = mapped_column(String(8), default="en")
    plan_name: Mapped[str | None] = mapped_column(String(64))

    # ---------------- Platform Context ---------------- #
    platform: Mapped[str] = mapped_column(String(32), default="shopify")

    # ---------------- Onboarding ---------------- #
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_step: Mapped[str | None] = mapped_column(String(64))