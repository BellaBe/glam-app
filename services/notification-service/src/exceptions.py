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
    UnsubscribedError
)
from shared.errors.base import (
    RateLimitedError,
    ValidationError,
    ConflictError
)

# Re-export all notification errors for convenience
__all__ = [
    # From shared.errors.notification
    'NotificationNotFoundError',
    'TemplateNotFoundError', 
    'TemplateRenderError',
    'InvalidRecipientError',
    'PreferencesNotFoundError',
    'EmailProviderError',
    'UnsubscribedError',
    
    # From shared.errors.base
    'RateLimitedError',
    'ValidationError',
    'ConflictError',
    
    # Aliases for backward compatibility (if needed)
    'NotificationNotFound',
    'TemplateNotFound',
    'PreferenceNotFound',
    'RateLimitExceeded',
    'TemplateError',
    'DuplicateTemplateName'
]

# Aliases for easier migration
NotificationNotFound = NotificationNotFoundError
TemplateNotFound = TemplateNotFoundError
PreferenceNotFound = PreferencesNotFoundError
RateLimitExceeded = RateLimitedError
TemplateError = TemplateRenderError

# Custom error for duplicate template name
class DuplicateTemplateName(ConflictError):
    """Template name already exists."""
    
    def __init__(self, message: str, template_name: str):
        super().__init__(
            message,
            conflicting_resource="template",
            current_state=f"Template with name '{template_name}' already exists"
        )