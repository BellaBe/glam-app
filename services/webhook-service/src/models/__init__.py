# services/webhook-service/src/models/__init__.py
"""Database models for webhook service."""

from shared.database.base import Base, TimestampedMixin
from .webhook import Webhook, WebhookStatus
from .platform_config import PlatformConfig

__all__ = [
    # Base (from shared)
    "Base",
    "TimestampedMixin",
    
    # Webhook models
    "Webhook",
    "WebhookStatus",
    
    # Platform models
    "PlatformConfig",
]