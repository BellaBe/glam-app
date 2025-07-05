# File: services/notification-service/src/models/__init__.py

"""Database models for notification service."""

from shared.database.base import Base, TimestampedMixin
from .base import ShopMixin
from .notification import Notification, NotificationStatus, NotificationProvider
from .template import NotificationTemplate, NotificationTemplateHistory, ChangeType

__all__ = [
    # Base (from shared)
    "Base",
    "TimestampedMixin",
    
    # Local mixins
    "ShopMixin",
    
    # Notification
    "Notification",
    "NotificationStatus",
    "NotificationProvider",
    
    # Template
    "NotificationTemplate",
    "NotificationTemplateHistory",
    "ChangeType",
]
