# services/webhook-service/src/utils/signature_validator.py
"""Signature validation utilities for webhooks."""

import hmac
import hashlib
import base64
from typing import Dict, Optional

from shared.utils.logger import ServiceLogger


class SignatureValidator:
    """Validates webhook signatures for different platforms."""
    
    def __init__(self, logger: ServiceLogger):
        self.logger = logger
    
    def validate_shopify_signature(
        self,
        body: bytes,
        headers: Dict[str, str],
        secret: str
    ) -> bool:
        """Validate Shopify HMAC signature."""
        
        signature = headers.get("X-Shopify-Hmac-Sha256")
        if not signature:
            self.logger.warning("Missing X-Shopify-Hmac-Sha256 header")
            return False
        
        try:
            # Calculate expected signature
            calculated = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).digest()
            expected = base64.b64encode(calculated).decode()
            
            # Use constant-time comparison to prevent timing attacks
            is_valid = hmac.compare_digest(expected, signature)
            
            if not is_valid:
                self.logger.warning(
                    "Shopify signature validation failed",
                    extra={
                        "expected_length": len(expected),
                        "received_length": len(signature),
                        "signature_prefix": signature[:10] if len(signature) >= 10 else signature
                    }
                )
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Shopify signature validation error: {e}")
            return False
    
    def validate_stripe_signature(
        self,
        body: bytes,
        headers: Dict[str, str],
        secret: str
    ) -> bool:
        """Validate Stripe webhook signature."""
        
        signature = headers.get("Stripe-Signature")
        if not signature:
            self.logger.warning("Missing Stripe-Signature header")
            return False
        
        try:
            # Parse Stripe signature format: t=timestamp,v1=signature
            sig_parts = {}
            for part in signature.split(','):
                if '=' in part:
                    key, value = part.split('=', 1)
                    sig_parts[key] = value
            
            timestamp = sig_parts.get('t')
            signature_v1 = sig_parts.get('v1')
            
            if not timestamp or not signature_v1:
                self.logger.warning("Invalid Stripe signature format")
                return False
            
            # Create payload for verification
            payload = f"{timestamp}.{body.decode('utf-8')}"
            
            # Calculate expected signature
            calculated = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison
            is_valid = hmac.compare_digest(calculated, signature_v1)
            
            if not is_valid:
                self.logger.warning("Stripe signature validation failed")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Stripe signature validation error: {e}")
            return False
    
    def validate_github_signature(
        self,
        body: bytes,
        headers: Dict[str, str],
        secret: str
    ) -> bool:
        """Validate GitHub webhook signature."""
        
        signature = headers.get("X-Hub-Signature-256")
        if not signature:
            self.logger.warning("Missing X-Hub-Signature-256 header")
            return False
        
        try:
            # GitHub signature format: sha256=<signature>
            if not signature.startswith('sha256='):
                self.logger.warning("Invalid GitHub signature format")
                return False
            
            expected_sig = signature[7:]  # Remove 'sha256=' prefix
            
            # Calculate expected signature
            calculated = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison
            is_valid = hmac.compare_digest(calculated, expected_sig)
            
            if not is_valid:
                self.logger.warning("GitHub signature validation failed")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"GitHub signature validation error: {e}")
            return False
    
    def validate_signature(
        self,
        platform: str,
        body: bytes,
        headers: Dict[str, str],
        secret: str
    ) -> bool:
        """Validate signature for any supported platform."""
        
        if platform == "shopify":
            return self.validate_shopify_signature(body, headers, secret)
        elif platform == "stripe":
            return self.validate_stripe_signature(body, headers, secret)
        elif platform == "github":
            return self.validate_github_signature(body, headers, secret)
        else:
            self.logger.warning(f"Unsupported platform for signature validation: {platform}")
            return False
