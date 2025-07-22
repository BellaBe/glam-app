# services/merchant-service/src/models/merchant.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from typing import List, Optional
from shared.database.base import Base, TimestampedMixin

from .merchant_status import MerchantStatus
from .merchant_configuration import MerchantConfiguration
from .installation_record import InstallationRecord

class Merchant(Base, TimestampedMixin):
    """Merchant profile model"""
    __tablename__ = "merchants"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Shopify Integration
    shop_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    shop_domain: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    shop_name: Mapped[str] = mapped_column(String(255), nullable=False)
    shop_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    shopify_access_token: Mapped[str] = mapped_column(String(255), nullable=False)  # Encrypted
    platform_api_version: Mapped[str] = mapped_column(String(50), default="2024-01")
    
    # Business Identity
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC")
    country: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # ISO country code
    currency: Mapped[str] = mapped_column(String(10), default="USD")  # ISO currency code
    language: Mapped[str] = mapped_column(String(10), default="en")
    plan_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Platform Context
    platform: Mapped[str] = mapped_column(String(50), default="shopify")
    
    # Onboarding
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_step: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    status: Mapped["MerchantStatus"] = relationship("MerchantStatus", back_populates="merchant", uselist=False)
    configuration: Mapped["MerchantConfiguration"] = relationship("MerchantConfiguration", back_populates="merchant", uselist=False)
    installation_records: Mapped[List["InstallationRecord"]] = relationship("InstallationRecord", back_populates="merchant")