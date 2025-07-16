# services/webhook-service/src/errors.py
"""Custom exceptions for webhook service."""

from typing import Optional


class WebhookServiceError(Exception):
    """Base exception for webhook service errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class InvalidSignatureError(WebhookServiceError):
    """Raised when webhook signature validation fails."""
    
    def __init__(self, message: str = "Invalid webhook signature"):
        super().__init__(message, "INVALID_SIGNATURE")


class WebhookValidationError(WebhookServiceError):
    """Raised when webhook payload validation fails."""
    
    def __init__(self, message: str = "Webhook validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


class PayloadTooLargeError(WebhookServiceError):
    """Raised when webhook payload exceeds size limit."""
    
    def __init__(self, message: str = "Webhook payload too large"):
        super().__init__(message, "PAYLOAD_TOO_LARGE")


class DuplicateWebhookError(WebhookServiceError):
    """Raised when duplicate webhook is detected."""
    
    def __init__(self, message: str = "Duplicate webhook detected"):
        super().__init__(message, "DUPLICATE_WEBHOOK")


class PlatformNotSupportedError(WebhookServiceError):
    """Raised when webhook platform is not supported."""
    
    def __init__(self, platform: str):
        super().__init__(f"Platform '{platform}' is not supported", "PLATFORM_NOT_SUPPORTED")


class WebhookProcessingError(WebhookServiceError):
    """Raised when webhook processing fails."""
    
    def __init__(self, message: str = "Webhook processing failed"):
        super().__init__(message, "PROCESSING_ERROR")