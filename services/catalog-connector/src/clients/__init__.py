# File: services/connector-service/src/clients/__init__.py

"""HTTP clients for external services."""

from .base import BaseAPIClient, APIResponse
from .shopify_client import ShopifyClient

__all__ = [
    "BaseAPIClient",
    "APIResponse",
    "ShopifyClient",
]