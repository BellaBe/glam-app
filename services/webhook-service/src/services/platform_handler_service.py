# services/webhook-service/src/services/platform_handler_service.py
"""Platform-specific webhook handling service."""

from __future__ import annotations

import hmac
import hashlib
import base64
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from shared.utils.logger import ServiceLogger

from ..config import WebhookServiceConfig


class WebhookHandler(ABC):
    """Abstract base class for platform-specific webhook handlers."""
    
    @abstractmethod
    def validate_signature(self, body: bytes, headers: Dict[str, str]) -> bool:
        """Validate webhook signature."""
        pass
    
    @abstractmethod
    def parse_webhook(self, body: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """Parse webhook payload."""
        pass
    
    @abstractmethod
    def get_shop_id(self, body: Dict[str, Any]) -> str:
        """Extract shop ID from webhook payload."""
        pass


class ShopifyWebhookHandler(WebhookHandler):
    """Handler for Shopify webhooks."""
    
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret
    
    def validate_signature(self, body: bytes, headers: Dict[str, str]) -> bool:
        """Validate Shopify HMAC signature."""
        
        signature = headers.get("X-Shopify-Hmac-Sha256")
        if not signature:
            return False
        
        calculated = hmac.new(
            self.webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
        expected = base64.b64encode(calculated).decode()
        
        return hmac.compare_digest(expected, signature)
    
    def parse_webhook(self, body: Dict[str, Any], topic: str) -> Dict[str, Any]:
        """Parse Shopify webhook payload."""
        return body  # Shopify sends clean JSON
    
    def get_shop_id(self, body: Dict[str, Any]) -> str:
        """Extract shop ID from Shopify payload."""
        
        # Try different possible shop identifier fields
        for field in ["shop_domain", "domain", "myshopify_domain"]:
            if field in body:
                return str(body[field])
        
        # Try nested shop object
        if "shop" in body and isinstance(body["shop"], dict):
            shop = body["shop"]
            for field in ["domain", "myshopify_domain", "id"]:
                if field in shop:
                    return str(shop[field])
        
        # Fallback to a default value
        return "unknown"


class PlatformHandlerService:
    """Service for managing platform-specific webhook handlers."""
    
    def __init__(self, config: WebhookServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
        self._handlers: Dict[str, WebhookHandler] = {}
        
        # Initialize platform handlers
        self._initialize_handlers()
    
    def _initialize_handlers(self) -> None:
        """Initialize platform-specific handlers."""
        
        # Shopify handler
        if self.config.shopify_webhook_secret:
            self._handlers["shopify"] = ShopifyWebhookHandler(
                webhook_secret=self.config.shopify_webhook_secret
            )
            self.logger.info("Shopify webhook handler initialized")
    
    def get_handler(self, platform: str) -> Optional[WebhookHandler]:
        """Get handler for specific platform."""
        return self._handlers.get(platform)
    
    def validate_webhook(
        self,
        platform: str,
        body: bytes,
        headers: Dict[str, str]
    ) -> bool:
        """Validate webhook signature for platform."""
        
        handler = self.get_handler(platform)
        if not handler:
            self.logger.warning(f"No handler found for platform: {platform}")
            return False
        
        try:
            return handler.validate_signature(body, headers)
        except Exception as e:
            self.logger.error(f"Signature validation failed for {platform}: {e}")
            return False
    
    def parse_webhook(
        self,
        platform: str,
        body: Dict[str, Any],
        topic: str
    ) -> Optional[Dict[str, Any]]:
        """Parse webhook payload for platform."""
        
        handler = self.get_handler(platform)
        if not handler:
            self.logger.warning(f"No handler found for platform: {platform}")
            return None
        
        try:
            return handler.parse_webhook(body, topic)
        except Exception as e:
            self.logger.error(f"Webhook parsing failed for {platform}: {e}")
            return None
    
    def get_shop_id(
        self,
        platform: str,
        body: Dict[str, Any]
    ) -> Optional[str]:
        """Get shop ID from webhook payload."""
        
        handler = self.get_handler(platform)
        if not handler:
            self.logger.warning(f"No handler found for platform: {platform}")
            return None
        
        try:
            return handler.get_shop_id(body)
        except Exception as e:
            self.logger.error(f"Shop ID extraction failed for {platform}: {e}")
            return None