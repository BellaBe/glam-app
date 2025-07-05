# # File: services/notification-service/src/models/base.py

"""Base model and common mixins for notification service models."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

# Import shared base and mixins
from shared.database.base import Base, TimestampedMixin


class ShopMixin:
    """Mixin for shop-related fields."""
    
    shop_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    shop_domain: Mapped[str] = mapped_column(String(255), nullable=False)