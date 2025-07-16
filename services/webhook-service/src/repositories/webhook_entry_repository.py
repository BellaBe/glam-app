# services/webhook-service/src/repositories/webhook_entry_repository.py
"""Repository for webhook entry operations."""

from __future__ import annotations

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.repository import Repository

from ..models.webhook_entry import WebhookEntry, WebhookStatus


class WebhookEntryRepository(Repository[WebhookEntry]):
    """Repository for webhook entry CRUD operations."""
    
    model = WebhookEntry
    
    async def find_by_platform_and_shop(
        self,
        session: AsyncSession,
        platform: str,
        shop_id: str,
        limit: int = 100
    ) -> List[WebhookEntry]:
        """Find webhook entries by platform and shop ID."""
        
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.platform == platform,
                    self.model.shop_id == shop_id
                )
            )
            .order_by(self.model.received_at.desc())
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_by_status(
        self,
        session: AsyncSession,
        status: WebhookStatus,
        limit: int = 100
    ) -> List[WebhookEntry]:
        """Find webhook entries by status."""
        
        stmt = (
            select(self.model)
            .where(self.model.status == status)
            .order_by(self.model.received_at.desc())
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_failed_webhooks(
        self,
        session: AsyncSession,
        max_attempts: int = 3,
        limit: int = 100
    ) -> List[WebhookEntry]:
        """Find failed webhook entries that haven't exceeded max attempts."""
        
        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.status == WebhookStatus.FAILED,
                    self.model.attempts < max_attempts
                )
            )
            .order_by(self.model.received_at.desc())
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_status(
        self,
        session: AsyncSession,
        webhook_id: UUID,
        status: WebhookStatus,
        error: Optional[str] = None,
        processed_at: Optional[datetime] = None
    ) -> Optional[WebhookEntry]:
        """Update webhook entry status."""
        
        webhook_entry = await self.find_by_id(session, webhook_id)
        if not webhook_entry:
            return None
        
        webhook_entry.status = status
        webhook_entry.attempts += 1
        
        if error:
            webhook_entry.error = error
        
        if processed_at:
            webhook_entry.processed_at = processed_at
        elif status == WebhookStatus.PROCESSED:
            webhook_entry.processed_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(webhook_entry)
        return webhook_entry
