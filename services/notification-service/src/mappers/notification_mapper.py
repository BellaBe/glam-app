# services/notification-service/src/mappers/notification_mapper.py
"""Mapper for notification schemas and models."""

from typing import Dict, Any, Optional
from uuid import UUID

from shared.api.correlation import get_correlation_context
from ..models import Notification, NotificationStatus, NotificationProvider
from ..schemas import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse
)
from shared.mappers.base import BaseMapper


class NotificationMapper(
    BaseMapper[
        Notification, NotificationCreate, NotificationUpdate, NotificationResponse
    ]
):
    """Maps between notification schemas and models."""

    def create_to_model(
        self,
        create_schema: NotificationCreate,
        **kwargs,
    ) -> Notification:
        subject = kwargs.get("subject")
        content = kwargs.get("content")
        provider = kwargs.get("provider", NotificationProvider.SENDGRID)
        unsubscribe_token = kwargs.get("unsubscribe_token")
        """
        Map NotificationCreate schema to Notification model.

        Args:
            create_schema: The create request schema
            subject: Rendered email subject
            content: Rendered email content (HTML)
            provider: Email service provider
            unsubscribe_token: Token for unsubscribe link

        Returns:
            Notification model instance
        """
        # Build metadata
        metadata = self._build_metadata(
            create_schema=create_schema, unsubscribe_token=unsubscribe_token
        )

        return Notification(
            merchant_id=create_schema.merchant_id,
            merchant_domain=create_schema.merchant_domain,
            recipient_email=create_schema.shop_email,
            type=create_schema.notification_type,
            subject=subject,
            content=content,
            status=NotificationStatus.PENDING,
            provider=provider,
            extra_metadata=metadata,
            retry_count=0,
        )

    def model_to_response(self, model: Notification) -> NotificationResponse:
        """Convert Notification model to response schema."""
        return NotificationResponse(
            id=model.id,
            merchant_id=model.merchant_id,
            merchant_domain=model.merchant_domain,
            shop_email=model.recipient_email,
            type=model.type,
            status=model.status,
            sent_at=model.sent_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _build_metadata(
        self, create_schema: NotificationCreate, unsubscribe_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build metadata dictionary from various sources."""
        metadata = {"dynamic_content": create_schema.dynamic_content}

        # Add correlation ID from context
        correlation_id = get_correlation_context()
        if correlation_id:
            metadata["correlation_id"] = {"correlation_id": correlation_id}

        # Add unsubscribe token if provided
        if unsubscribe_token:
            metadata["unsubscribe_token"] = {"unsubscribe_token": unsubscribe_token}

        # Merge extra metadata from request
        if create_schema.extra_metadata:
            metadata.update(create_schema.extra_metadata)

        return metadata
