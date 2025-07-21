# services/webhook-service/src/mappers/webhook_entry_mapper.py
"""Mapper for webhook entry model to response schemas."""

from __future__ import annotations

from typing import List
from uuid import UUID

from shared.mappers.base import BaseMapper

from ..models.webhook_entry import WebhookEntry
from ..schemas.webhook import WebhookEntryResponse, CreateWebhookSchema


class WebhookEntryMapper(BaseMapper[WebhookEntry, CreateWebhookSchema, None, WebhookEntryResponse]): #type: ignore
    """Mapper for webhook entry operations."""
    
    
    def create_to_model(self, create_schema: CreateWebhookSchema, **kwargs) -> WebhookEntry:
        """Convert create schema to webhook entry model."""
        webhook_entry_data = WebhookEntry(
            id=UUID(),
            platform=create_schema.platform,
            topic=create_schema.topic,
            shop_id=create_schema.shop_id,
            status=create_schema.status,
            attempts=create_schema.attempts,
            error=create_schema.error,
            received_at=create_schema.received_at,
            processed_at=create_schema.processed_at,
        )
        return webhook_entry_data

    def model_to_response(self, model: WebhookEntry) -> WebhookEntryResponse:
        """Convert webhook entry model to response schema."""
        return WebhookEntryResponse(
            id=model.id,
            platform=model.platform,
            topic=model.topic,
            shop_id=model.shop_id,
            status=model.status,
            attempts=model.attempts,
            error=model.error,
            received_at=model.received_at,
            processed_at=model.processed_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def to_response_list(self, models: List[WebhookEntry]) -> List[WebhookEntryResponse]:
        """Convert list of webhook entries to response schemas."""
        return [self.model_to_response(model) for model in models]
    
    
