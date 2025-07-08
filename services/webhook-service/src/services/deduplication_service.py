# services/webhook-service/src/services/deduplication_service.py
"""Service for webhook deduplication using Redis."""

from typing import Optional
import redis.asyncio as redis

from shared.utils.logger import ServiceLogger


class DeduplicationService:
    """Handle webhook deduplication via Redis"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        ttl_hours: int = 24,
        logger: Optional[ServiceLogger] = None
    ):
        self.redis = redis_client
        self.ttl_seconds = ttl_hours * 3600
        self.logger = logger or ServiceLogger(__name__)
        self.key_prefix = "webhook:dedup:"
    
    async def is_duplicate(self, idempotency_key: str) -> bool:
        """Check if webhook has been seen before"""
        key = f"{self.key_prefix}{idempotency_key}"
        
        try:
            exists = await self.redis.exists(key)
            return bool(exists)
        except Exception as e:
            self.logger.error(
                f"Failed to check deduplication: {e}",
                extra={"idempotency_key": idempotency_key}
            )
            # Fail open - process webhook if Redis fails
            return False
    
    async def mark_as_seen(self, idempotency_key: str) -> bool:
        """Mark webhook as processed"""
        key = f"{self.key_prefix}{idempotency_key}"
        
        try:
            # Set with TTL
            await self.redis.setex(
                key,
                self.ttl_seconds,
                "1"
            )
            return True
        except Exception as e:
            self.logger.error(
                f"Failed to mark as seen: {e}",
                extra={"idempotency_key": idempotency_key}
            )
            return False
    
    async def remove(self, idempotency_key: str) -> bool:
        """Remove idempotency key (for testing/replay)"""
        key = f"{self.key_prefix}{idempotency_key}"
        
        try:
            result = await self.redis.delete(key)
            return bool(result)
        except Exception as e:
            self.logger.error(
                f"Failed to remove key: {e}",
                extra={"idempotency_key": idempotency_key}
            )
            return False