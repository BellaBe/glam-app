# services/webhook-service/src/services/auth_service.py
"""Authentication service for webhook validation."""

import base64
import hashlib
import hmac
from typing import Optional
from abc import ABC, abstractmethod

from shared.utils.logger import ServiceLogger
from ..models.webhook_entry import WebhookSource
from ..repositories.platform_config_repository import PlatformConfigRepository


class WebhookAuthService:
    """Service for webhook authentication"""
    
    def __init__(
        self,
        platform_config_repo: PlatformConfigRepository,
        shopify_secret: str,
        stripe_secret: Optional[str] = None,
        logger: Optional[ServiceLogger] = None
    ):
        self.platform_config_repo = platform_config_repo
        self.shopify_secret = shopify_secret
        self.stripe_secret = stripe_secret
        self.logger = logger or ServiceLogger(__name__)
    
    def validate_shopify_webhook(
        self, 
        body: bytes, 
        signature: str
    ) -> bool:
        """Validate Shopify webhook HMAC signature"""
        try:
            digest = hmac.new(
                self.shopify_secret.encode(), 
                body, 
                hashlib.sha256
            ).digest()
            expected = base64.b64encode(digest).decode()
            
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            self.logger.error(
                "Failed to validate Shopify webhook",
                extra={"error": str(e)}
            )
            return False
    
    def validate_stripe_webhook(
        self, 
        body: bytes, 
        signature: str,
        timestamp: str
    ) -> bool:
        """Validate Stripe webhook signature"""
        if not self.stripe_secret:
            self.logger.error("Stripe webhook secret not configured")
            return False
        
        try:
            # Stripe signature format: t=timestamp,v1=signature
            signed_payload = f"{timestamp}.{body.decode('utf-8')}"
            expected_sig = hmac.new(
                self.stripe_secret.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Extract v1 signature from header
            sig_parts = dict(part.split('=') for part in signature.split(','))
            provided_sig = sig_parts.get('v1', '')
            
            return hmac.compare_digest(expected_sig, provided_sig)
        except Exception as e:
            self.logger.error(
                "Failed to validate Stripe webhook",
                extra={"error": str(e)}
            )
            return False
    
    async def validate_webhook(
        self,
        source: WebhookSource,
        body: bytes,
        headers: dict
    ) -> bool:
        """Validate webhook based on source"""
        if source == WebhookSource.SHOPIFY:
            signature = headers.get('x-shopify-hmac-sha256', '')
            return self.validate_shopify_webhook(body, signature)
        
        elif source == WebhookSource.STRIPE:
            signature = headers.get('stripe-signature', '')
            # Extract timestamp from signature header
            sig_parts = dict(part.split('=') for part in signature.split(','))
            timestamp = sig_parts.get('t', '')
            return self.validate_stripe_webhook(body, signature, timestamp)
        
        else:
            self.logger.warning(f"Unknown webhook source: {source}")
            return False