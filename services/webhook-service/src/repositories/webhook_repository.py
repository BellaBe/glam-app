# services/webhook-service/src/repositories/webhook_repository.py
"""Repository for webhook entry operations."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.database.repository import Repository
from ..models.webhook_entry import WebhookEntry, WebhookStatus, WebhookSource


class WebhookRepository(Repository[WebhookEntry]):
    """Repository for webhook operations"""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(WebhookEntry, session_factory)

    async def create_entry(
        self,
        source: WebhookSource,
        topic: str,
        headers: dict,
        payload: dict,
        hmac_signature: str,
        idempotency_key: str,
        merchant_id: Optional[str] = None,
        merchant_domain: Optional[str] = None,
    ) -> WebhookEntry:
        """Create a new webhook entry"""
        async with self.session_factory() as session:
            entry = WebhookEntry(
                source=source,
                topic=topic,
                headers=headers,
                payload=payload,
                hmac_signature=hmac_signature,
                idempotency_key=idempotency_key,
                merchant_id=merchant_id,
                merchant_domain=merchant_domain,
                status=WebhookStatus.RECEIVED,
            )

            session.add(entry)
            await session.commit()
            await session.refresh(entry)

            return entry

    async def find_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[WebhookEntry]:
        """Find webhook by idempotency key"""
        async with self.session_factory() as session:
            stmt = select(WebhookEntry).where(
                WebhookEntry.idempotency_key == idempotency_key
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def mark_as_processing(self, entry_id: UUID) -> bool:
        """Mark webhook as processing"""
        async with self.session_factory() as session:
            stmt = (
                update(WebhookEntry)
                .where(
                    and_(
                        WebhookEntry.id == entry_id,
                        WebhookEntry.status == WebhookStatus.RECEIVED,
                    )
                )
                .values(
                    status=WebhookStatus.PROCESSING, attempts=WebhookEntry.attempts + 1
                )
            )

            result = await session.execute(stmt)
            await session.commit()

            return result.rowcount > 0

    async def mark_as_processed(self, entry_id: UUID) -> bool:
        """Mark webhook as successfully processed"""
        async with self.session_factory() as session:
            stmt = (
                update(WebhookEntry)
                .where(WebhookEntry.id == entry_id)
                .values(
                    status=WebhookStatus.PROCESSED,
                    processed_at=datetime.now(timezone.utc),
                    error=None,
                )
            )

            result = await session.execute(stmt)
            await session.commit()

            return result.rowcount > 0

    async def mark_as_failed(self, entry_id: UUID, error: str) -> bool:
        """Mark webhook as failed"""
        async with self.session_factory() as session:
            stmt = (
                update(WebhookEntry)
                .where(WebhookEntry.id == entry_id)
                .values(
                    status=WebhookStatus.FAILED,
                    error=error,
                    processed_at=datetime.now(timezone.utc),
                )
            )

            result = await session.execute(stmt)
            await session.commit()

            return result.rowcount > 0

    async def get_failed_webhooks(
        self, max_attempts: int = 5, limit: int = 100
    ) -> List[WebhookEntry]:
        """Get failed webhooks for retry"""
        async with self.session_factory() as session:
            stmt = (
                select(WebhookEntry)
                .where(
                    and_(
                        WebhookEntry.status == WebhookStatus.FAILED,
                        WebhookEntry.attempts < max_attempts,
                    )
                )
                .order_by(WebhookEntry.created_at)
                .limit(limit)
            )

            result = await session.execute(stmt)
            return list(result.scalars())
