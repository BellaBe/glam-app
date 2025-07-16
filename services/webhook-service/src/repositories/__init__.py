# services/webhook-service/src/repositories/__init__.py
"""Repositories for webhook service."""

from .webhook_entry_repository import WebhookEntryRepository
from .platform_configuration_repository import PlatformConfigurationRepository

__all__ = [
    "WebhookEntryRepository",
    "PlatformConfigurationRepository",
]

