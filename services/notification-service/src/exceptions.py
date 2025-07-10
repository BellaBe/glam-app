# File: services/notification-service/src/exceptions.py
"""
Notification service exceptions using shared error classes.

All exceptions are re-exported from shared.errors for consistency
across the platform.
"""

from shared.errors.notification import (
    NotificationNotFoundError,
    TemplateNotFoundError,
    TemplateRenderError,
    InvalidRecipientError,
    PreferencesNotFoundError,
    EmailProviderError,
    UnsubscribedError,
)
from shared.errors.base import (
    RateLimitedError,
    ValidationError,
    ConflictError,
    DomainError,
)

# Re-export all notification errors for convenience
__all__ = [
    # From shared.errors.notification
    "NotificationNotFoundError",
    "TemplateNotFoundError",
    "TemplateRenderError",
    "InvalidRecipientError",
    "PreferencesNotFoundError",
    "EmailProviderError",
    "UnsubscribedError",
    # From shared.errors.base
    "RateLimitedError",
    "ValidationError",
    "ConflictError",
]


# Custom error for duplicate template name
class DuplicateTemplateName(ConflictError):
    """Template name already exists."""

    def __init__(self, message: str, template_name: str):
        super().__init__(
            message,
            conflicting_resource="template",
            current_state=f"Template with name '{template_name}' already exists",
        )


class PreferenceAlreadyExists(DomainError):
    """Raised when trying to create preferences that already exist"""

    def __init__(self, message: str, merchant_id: str):
        super().__init__(
            message=message,
            code="PREFERENCE_ALREADY_EXISTS",
            status=409,  # Conflict
            details={"merchant_id": merchant_id},
        )


class TemplateAlreadyExistsError(DomainError):
    """Raised when trying to create templat that already exist"""

    def __init__(self, message: str, template_id: str):
        super().__init__(
            message=message,
            code="TEMPLATE_ALREADY_EXISTS",
            status=409,
            details={"template_id": template_id},
        )


class RateLimitExceededError(RateLimitedError):
    """Rate limit exceeded for notification service"""

    def __init__(self, message: str, recipient_email: str, notification_type: str):
        super().__init__(
            message=message,
            recipient_email=recipient_email,
            notification_type=notification_type,
        )
