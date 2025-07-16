# services/webhook-service/src/services/webhook_service.py
"""Core webhook processing service."""

from __future__ import annotations

import json
import hashlib
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from shared.utils.logger import ServiceLogger
from shared.database.dependencies import get_db_session

from ..config import WebhookServiceConfig
from ..models.webhook_entry import WebhookEntry, WebhookStatus
from ..repositories.webhook_entry_repository import WebhookEntryRepository
from ..repositories.platform_configuration_repository import PlatformConfigurationRepository
from ..events.publishers import WebhookEventPublisher
from ..events.domain_events import (
    AppUninstalledEvent,
    CatalogItemCreatedEvent,
    OrderCreatedEvent,
    InventoryUpdatedEvent
)


class WebhookService:
    """Core service for webhook processing."""
    
    def __init__(
        self,
        webhook_entry_repo: WebhookEntryRepository,
        platform_config_repo: PlatformConfigurationRepository,
        redis_client: redis.Redis,
        publisher: WebhookEventPublisher,
        config: WebhookServiceConfig,
        logger: ServiceLogger
    ):
        self.webhook_entry_repo = webhook_entry_repo
        self.platform_config_repo = platform_config_repo
        self.redis_client = redis_client
        self.publisher = publisher
        self.config = config
        self.logger = logger
    
    async def process_webhook(
        self,
        platform: str,
        topic: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        signature: str
    ) -> WebhookEntry:
        """
        Process an incoming webhook.
        
        Returns:
            WebhookEntry: The created webhook entry
        """
        
        # Extract shop ID from payload
        shop_id = self._extract_shop_id(platform, payload)
        
        # Check for duplicates
        webhook_id = self._generate_webhook_id(platform, topic, shop_id, payload)
        if await self._is_duplicate(webhook_id):
            self.logger.info(
                f"Duplicate webhook detected",
                extra={
                    "platform": platform,
                    "topic": topic,
                    "shop_id": shop_id,
                    "webhook_id": webhook_id
                }
            )
            # Return existing webhook entry or create a dummy one
            # For now, we'll create a new entry but mark it as duplicate in logs
        
        # Create webhook entry
        async with get_db_session() as session:
            webhook_entry = WebhookEntry(
                platform=platform,
                topic=topic,
                shop_id=shop_id,
                payload=payload,
                headers=headers,
                signature=signature,
                status=WebhookStatus.RECEIVED,
                received_at=datetime.utcnow()
            )
            
            await self.webhook_entry_repo.create(session, webhook_entry)
            
            try:
                # Mark as processing
                webhook_entry.status = WebhookStatus.PROCESSING
                await session.commit()
                
                # Transform and publish domain event
                domain_event = self._transform_to_domain_event(platform, topic, payload, shop_id)
                if domain_event:
                    await self.publisher.publish_event(domain_event)
                    self.logger.info(
                        f"Domain event published",
                        extra={
                            "event_type": domain_event.event_type,
                            "shop_id": shop_id,
                            "webhook_id": str(webhook_entry.id)
                        }
                    )
                
                # Mark as processed
                webhook_entry.status = WebhookStatus.PROCESSED
                webhook_entry.processed_at = datetime.utcnow()
                await session.commit()
                
                # Store in Redis for deduplication
                await self._store_for_deduplication(webhook_id)
                
                self.logger.info(
                    f"Webhook processed successfully",
                    extra={
                        "platform": platform,
                        "topic": topic,
                        "shop_id": shop_id,
                        "webhook_id": str(webhook_entry.id)
                    }
                )
                
            except Exception as e:
                # Mark as failed
                webhook_entry.status = WebhookStatus.FAILED
                webhook_entry.error = str(e)
                await session.commit()
                
                self.logger.error(
                    f"Webhook processing failed",
                    extra={
                        "platform": platform,
                        "topic": topic,
                        "shop_id": shop_id,
                        "webhook_id": str(webhook_entry.id),
                        "error": str(e)
                    },
                    exc_info=True
                )
                raise
            
            await session.refresh(webhook_entry)
            return webhook_entry
    
    def _extract_shop_id(self, platform: str, payload: Dict[str, Any]) -> str:
        """Extract shop ID from webhook payload based on platform."""
        
        if platform == "shopify":
            # Try multiple possible shop identifier fields
            for field in ["shop_domain", "domain", "myshopify_domain"]:
                if field in payload:
                    return str(payload[field])
            
            # Fallback: extract from nested objects
            if "shop" in payload and isinstance(payload["shop"], dict):
                for field in ["domain", "myshopify_domain", "id"]:
                    if field in payload["shop"]:
                        return str(payload["shop"][field])
        
        # Generic fallback
        for field in ["shop_id", "store_id", "merchant_id", "account_id"]:
            if field in payload:
                return str(payload[field])
        
        # Ultimate fallback - use a hash of the payload
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.md5(payload_str.encode()).hexdigest()[:16]
    
    def _generate_webhook_id(
        self,
        platform: str,
        topic: str,
        shop_id: str,
        payload: Dict[str, Any]
    ) -> str:
        """Generate a unique ID for webhook deduplication."""
        
        # Try to use platform-specific webhook ID first
        if platform == "shopify" and "id" in payload:
            return f"{platform}:{topic}:{shop_id}:{payload['id']}"
        
        # Fallback to hash-based ID
        content = f"{platform}:{topic}:{shop_id}:{json.dumps(payload, sort_keys=True)}"
        webhook_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{platform}:{topic}:{shop_id}:{webhook_hash}"
    
    async def _is_duplicate(self, webhook_id: str) -> bool:
        """Check if webhook has already been processed."""
        
        try:
            result = await self.redis_client.get(f"webhook:processed:{webhook_id}")
            return result is not None
        except Exception as e:
            self.logger.warning(f"Redis deduplication check failed: {e}")
            return False
    
    async def _store_for_deduplication(self, webhook_id: str) -> None:
        """Store webhook ID in Redis for deduplication."""
        
        try:
            ttl_seconds = self.config.webhook_dedup_ttl_hours * 3600
            await self.redis_client.setex(
                f"webhook:processed:{webhook_id}",
                ttl_seconds,
                "1"
            )
        except Exception as e:
            self.logger.warning(f"Redis deduplication storage failed: {e}")
    
    def _transform_to_domain_event(
        self,
        platform: str,
        topic: str,
        payload: Dict[str, Any],
        shop_id: str
    ) -> Optional[Any]:
        """Transform webhook payload to domain event."""
        
        if platform != "shopify":
            self.logger.info(f"No transformation available for platform: {platform}")
            return None
        
        # Shopify event transformations
        if topic == "app/uninstalled":
            return AppUninstalledEvent.create(
                shop_id=shop_id,
                shop_domain=payload.get("domain", shop_id),
                timestamp=datetime.utcnow()
            )
        
        elif topic in ["products/create"]:
            return CatalogItemCreatedEvent.create(
                shop_id=shop_id,
                item_id=str(payload.get("id", "")),
                external_id=str(payload.get("id", ""))
            )
        
        elif topic == "orders/create":
            return OrderCreatedEvent.create(
                shop_id=shop_id,
                order_id=str(payload.get("id", "")),
                total=float(payload.get("total_price", 0.0)),
                items=payload.get("line_items", [])
            )
        
        elif topic == "inventory_levels/update":
            return InventoryUpdatedEvent.create(
                shop_id=shop_id,
                item_id=str(payload.get("inventory_item_id", "")),
                location_id=str(payload.get("location_id", "")),
                available=int(payload.get("available", 0))
            )
        
        else:
            self.logger.info(f"No transformation available for topic: {topic}")
            return None
