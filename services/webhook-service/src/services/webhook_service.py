import hmac
import hashlib
import base64
from typing import Optional, Tuple
from shared.utils.logger import ServiceLogger
from shared.api.correlation import get_correlation_context
from ..config import ServiceConfig
from ..models.enums import WebhookPlatform


class WebhookService:
    """Business logic for webhook processing"""
    
    def __init__(self, config: ServiceConfig, logger: ServiceLogger):
        self.config = config
        self.logger = logger
    
    def validate_hmac(
        self,
        raw_body: bytes,
        header_hmac: str,
        primary_secret: str,
        next_secret: Optional[str] = None
    ) -> Tuple[Optional[str], bool]:
        """Validate HMAC with secret rotation support"""
        # Try primary secret
        computed_hmac = self._compute_hmac(raw_body, primary_secret)
        if self._constant_time_compare(computed_hmac, header_hmac):
            return ('primary', True)
        
        # Try rotation secret
        if next_secret:
            computed_hmac_next = self._compute_hmac(raw_body, next_secret)
            if self._constant_time_compare(computed_hmac_next, header_hmac):
                return ('next', True)
        
        return (None, False)
    
    def _compute_hmac(self, raw_body: bytes, secret: str) -> str:
        """Compute HMAC-SHA256 and return base64 encoded"""
        hash_obj = hmac.new(
            secret.encode('utf-8'),
            raw_body,
            hashlib.sha256
        )
        return base64.b64encode(hash_obj.digest()).decode('utf-8')
    
    def _constant_time_compare(self, a: str, b: str) -> bool:
        """Constant time string comparison to prevent timing attacks"""
        if len(a) != len(b):
            return False
        
        result = 0
        for char_a, char_b in zip(a, b):
            result |= ord(char_a) ^ ord(char_b)
        
        return result == 0
    
    def validate_content_type(self, content_type: Optional[str]) -> bool:
        """Validate content type, ignoring charset"""
        if not content_type:
            return False
        
        # Handle "application/json; charset=utf-8"
        main_type = content_type.split(';', 1)[0].strip().lower()
        return main_type == 'application/json'
    
    def validate_shop_domain(self, domain: str) -> bool:
        """Validate shop domain format"""
        return domain.lower().endswith('.myshopify.com')
    
    def is_shopify_ip(self, client_ip: str) -> bool:
        """Check if IP is from Shopify (simplified for now)"""
        # In production, this would check against actual Shopify IP ranges
        # For now, return True if no IPs configured
        if not self.config.webhook_shopify_ips:
            return True
        
        return client_ip in self.config.webhook_shopify_ips
    
    def extract_canonical_headers(self, headers: dict) -> dict:
        """Extract and canonicalize required headers"""
        # Case-insensitive header lookup
        canonical = {}
        header_map = {k.lower(): v for k, v in headers.items()}
        
        # Required headers with canonical names
        required_headers = {
            'x-shopify-hmac-sha256': 'X-Shopify-Hmac-Sha256',
            'x-shopify-topic': 'X-Shopify-Topic',
            'x-shopify-shop-domain': 'X-Shopify-Shop-Domain',
            'x-shopify-webhook-id': 'X-Shopify-Webhook-Id',
            'x-shopify-api-version': 'X-Shopify-Api-Version',
        }
        
        for lower_name, canonical_name in required_headers.items():
            if lower_name in header_map:
                canonical[canonical_name] = header_map[lower_name]
        
        return canonical


