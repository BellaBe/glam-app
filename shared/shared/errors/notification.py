# -------------------------------
# shared/errors/notification.py
# -------------------------------

from uuid import UUID

"""Notification service specific errors."""

from typing import Optional
from .base import NotFoundError, ValidationError, InfrastructureError, ConflictError


class NotificationNotFoundError(NotFoundError):
    """Notification not found."""

    code = "NOTIFICATION_NOT_FOUND"

    def __init__(
        self,
        message: str,
        *,
        notification_id: Optional[UUID] = None,
        merchant_id: Optional[UUID] = None,
        **kwargs
    ):
        super().__init__(
            message, resource="notification", resource_id=notification_id, **kwargs
        )

        if merchant_id:
            self.details["merchant_id"] = merchant_id


class TemplateNotFoundError(NotFoundError):
    """Email template not found."""

    code = "TEMPLATE_NOT_FOUND"

    def __init__(
        self,
        message: str,
        *,
        template_name: Optional[str] = None,
        template_type: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message, resource="template", resource_id=template_name, **kwargs
        )

        if template_type:
            self.details["template_type"] = template_type


class TemplateRenderError(ValidationError):
    """Failed to render email template."""

    code = "TEMPLATE_RENDER_ERROR"

    def __init__(
        self,
        message: str,
        *,
        template_name: Optional[str] = None,
        missing_variables: Optional[list] = None,
        render_error: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if template_name:
            self.details["template_name"] = template_name
        if missing_variables:
            self.details["missing_variables"] = missing_variables
        if render_error:
            self.details["render_error"] = render_error


class InvalidRecipientError(ValidationError):
    """Invalid recipient email address."""

    code = "INVALID_RECIPIENT"

    def __init__(
        self,
        message: str,
        *,
        recipient: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, field="recipient", value=recipient, **kwargs)

        if reason:
            self.details["reason"] = reason


class PreferencesNotFoundError(NotFoundError):
    """Notification preferences not found."""

    code = "PREFERENCES_NOT_FOUND"

    def __init__(self, message: str, *, user_id: Optional[str] = None, **kwargs):
        super().__init__(
            message, resource="notification_preferences", resource_id=user_id, **kwargs
        )


class EmailProviderError(InfrastructureError):
    """Email provider API error."""

    code = "EMAIL_PROVIDER_ERROR"

    def __init__(
        self,
        message: str,
        *,
        provider: Optional[str] = None,
        provider_error_code: Optional[str] = None,
        provider_message: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, service=provider, **kwargs)

        if provider_error_code:
            self.details["provider_error_code"] = provider_error_code
        if provider_message:
            self.details["provider_message"] = provider_message


class UnsubscribedError(ConflictError):
    """Recipient has unsubscribed."""

    code = "UNSUBSCRIBED"

    def __init__(
        self,
        message: str = "Recipient has unsubscribed from notifications",
        *,
        user_id: Optional[str] = None,
        notification_type: Optional[str] = None,
        unsubscribed_at: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)

        if user_id:
            self.details["user_id"] = user_id
        if notification_type:
            self.details["notification_type"] = notification_type
        if unsubscribed_at:
            self.details["unsubscribed_at"] = unsubscribed_at
