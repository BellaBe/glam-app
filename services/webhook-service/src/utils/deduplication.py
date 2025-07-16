# services/webhook-service/src/utils/deduplication.py
"""Deduplication utilities for webhook service."""

import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import redis.asyncio as redis

from shared.utils.logger import ServiceLogger


class DeduplicationManager:
    """Manages webhook deduplication using Redis."""
    
    def __init__(self, redis_client: redis.Redis, logger: ServiceLogger, ttl_hours: int = 24):
        self.redis_client = redis_client
        self.logger = logger
        self.ttl_seconds = ttl_hours * 3600
        self.key_prefix = "webhook:dedup"
    
    def generate_dedup_key(
        self,
        platform: str,
        topic: str,
        shop_id: str,
        payload: Dict[str, Any],
        webhook_id: Optional[str] = None
    ) -> str:
        """Generate deduplication key for webhook."""
        
        if webhook_id:
            # Use platform-provided webhook ID if available
            return f"{self.key_prefix}:{platform}:{topic}:{shop_id}:{webhook_id}"
        
        # Fallback to content-based hash
        content = {
            "platform": platform,
            "topic": topic,
            "shop_id": shop_id,
            "payload": payload
        }
        
        # Create deterministic hash
        content_str = json.dumps(content, sort_keys=True, separators=(',', ':'))
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]
        
        return f"{self.key_prefix}:{platform}:{topic}:{shop_id}:{content_hash}"
    
    async def is_duplicate(self, dedup_key: str) -> bool:
        """Check if webhook is a duplicate."""
        
        try:
            result = await self.redis_client.get(dedup_key)
            return result is not None
        except Exception as e:
            self.logger.warning(f"Deduplication check failed: {e}")
            return False
    
    async def mark_processed(self, dedup_key: str, webhook_id: str) -> None:
        """Mark webhook as processed."""
        
        try:
            await self.redis_client.setex(
                dedup_key,
                self.ttl_seconds,
                json.dumps({
                    "webhook_id": webhook_id,
                    "processed_at": datetime.utcnow().isoformat()
                })
            )
        except Exception as e:
            self.logger.warning(f"Failed to mark webhook as processed: {e}")
    
    async def get_processed_info(self, dedup_key: str) -> Optional[Dict[str, Any]]:
        """Get information about processed webhook."""
        
        try:
            result = await self.redis_client.get(dedup_key)
            if result:
                return json.loads(result)
            return None
        except Exception as e:
            self.logger.warning(f"Failed to get processed info: {e}")
            return None
    
    async def cleanup_expired(self) -> int:
        """Clean up expired deduplication entries."""
        
        try:
            # Get all deduplication keys
            keys = await self.redis_client.keys(f"{self.key_prefix}:*")
            
            if not keys:
                return 0
            
            # Check TTL for each key and count expired ones
            expired_count = 0
            for key in keys:
                ttl = await self.redis_client.ttl(key)
                if ttl == -1:  # Key exists but has no TTL
                    await self.redis_client.delete(key)
                    expired_count += 1
            
            return expired_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired entries: {e}")
            return 0