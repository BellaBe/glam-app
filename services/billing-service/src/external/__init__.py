# services/billing-service/src/external/__init__.py
"""External integrations for billing service."""
from .shopify_billing_client import ShopifyBillingClient
__all__ = [
    "ShopifyBillingClient",
]