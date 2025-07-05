# -------------------------------
# services/notification-service/src/mappers/notification_mapper.py
# -------------------------------

"""Mapper for notification schemas and models."""

from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from shared.api.correlation import get_correlation_context
from ..models import Notification, NotificationStatus, NotificationProvider
from ..schemas import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationDetailResponse
)
from .base import BaseMapper


class NotificationMapper(BaseMapper[
    Notification,
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse
]):
    """Maps between notification schemas and models."""
    
    def create_to_model( # type: ignore
        self,
        create_schema: NotificationCreate,
        *,
        subject: str,
        content: str,
        provider: NotificationProvider = NotificationProvider.SENDGRID,
        unsubscribe_token: Optional[str] = None
    ) -> Notification:
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
            create_schema=create_schema,
            unsubscribe_token=unsubscribe_token
        )
        
        return Notification(
            # Shop information
            shop_id=str(create_schema.shop_id),
            shop_domain=create_schema.shop_domain,
            
            # Recipient information
            recipient_email=create_schema.shop_email,
            type=create_schema.notification_type,
            
            # Email content
            subject=subject,
            content=content,
            
            # Status and provider
            status=NotificationStatus.PENDING,
            provider=provider,
            
            # Metadata
            extra_metadata=metadata,
            
            # Initialize counters
            retry_count=0
        )
    
    def model_to_response(self, model: Notification) -> NotificationResponse:
        """Convert Notification model to response schema."""
        return NotificationResponse(
            id=UUID(str(model.id)),
            shop_id=UUID(model.shop_id),
            shop_domain=model.shop_domain,
            shop_email=model.recipient_email,
            type=model.type,
            status=model.status,
            sent_at=model.sent_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def model_to_detail_response(self, model: Notification) -> NotificationDetailResponse:
        """Convert Notification model to detailed response schema."""
        return NotificationDetailResponse(
            id=UUID(str(model.id)),
            shop_id=UUID(model.shop_id),
            shop_domain=model.shop_domain,
            shop_email=model.recipient_email,
            type=model.type,
            status=model.status,
            sent_at=model.sent_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            content=model.content,
            provider=model.provider,
            provider_message_id=model.provider_message_id,
            error_message=model.error_message,
            retry_count=model.retry_count,
            extra_metadata=model.extra_metadata or {}
        )
    
    def update_to_model_dict(self, update_schema: NotificationUpdate) -> dict:
        """
        Convert update schema to dictionary for model updates.
        
        Maps schema fields to model fields and handles special cases.
        """
        update_dict = {}
        
        if update_schema.status is not None:
            update_dict["status"] = update_schema.status
            
        if update_schema.provider_message_id is not None:
            update_dict["provider_message_id"] = update_schema.provider_message_id
            
        if update_schema.error_message is not None:
            update_dict["error_message"] = update_schema.error_message
            
        if update_schema.sent_at is not None:
            update_dict["sent_at"] = update_schema.sent_at
            
        return update_dict
    
    def _build_metadata(
        self,
        create_schema: NotificationCreate,
        unsubscribe_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build metadata dictionary from various sources."""
        metadata = {
            "dynamic_content": create_schema.dynamic_content
        }
        
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
