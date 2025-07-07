# services/scheduler-service/src/utils/distributed_lock.py
"""Distributed lock implementation using Redis"""

import asyncio
import time
from typing import Optional, Dict
from uuid import uuid4

import redis.asyncio as redis
from shared.utils.logger import ServiceLogger


class DistributedLock:
    """Redis-based distributed lock for preventing duplicate job execution"""
    
    def __init__(self, redis_url: str, logger: ServiceLogger):
        self.redis_url = redis_url
        self.logger = logger
        self._redis_client: Optional[redis.Redis] = None
        self._locks: Dict[str, str] = {}  # key -> lock_id mapping
    
    async def connect(self):
        """Connect to Redis"""
        self._redis_client = await redis.from_url(
            self.redis_url,
            decode_responses=True
        )
        self.logger.info("Connected to Redis for distributed locking")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
        self.logger.info("Disconnected from Redis")
    
    async def acquire(
        self,
        key: str,
        ttl: int = 300,
        retry_delay: float = 0.1,
        max_retries: int = 50
    ) -> bool:
        """
        Acquire a distributed lock
        
        Args:
            key: Lock key
            ttl: Time to live in seconds
            retry_delay: Delay between retries in seconds
            max_retries: Maximum number of retries
            
        Returns:
            True if lock acquired, False otherwise
        """
        if not self._redis_client:
            raise RuntimeError("Redis client not connected")
        
        lock_id = str(uuid4())
        
        for attempt in range(max_retries):
            try:
                # Try to set the lock with NX (only if not exists)
                acquired = await self._redis_client.set(
                    key,
                    lock_id,
                    nx=True,
                    ex=ttl
                )
                
                if acquired:
                    self._locks[key] = lock_id
                    self.logger.debug(
                        f"Acquired lock: {key}",
                        extra={"lock_id": lock_id, "ttl": ttl}
                    )
                    return True
                
                # Lock exists, check if it's ours (in case of reconnection)
                current_lock = await self._redis_client.get(key)
                if current_lock == lock_id:
                    self._locks[key] = lock_id
                    return True
                
            except Exception as e:
                self.logger.error(
                    f"Error acquiring lock: {key}",
                    extra={"error": str(e), "attempt": attempt}
                )
            
            # Wait before retrying
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
        
        self.logger.warning(
            f"Failed to acquire lock after {max_retries} attempts: {key}"
        )
        return False
    
    async def release(self, key: str) -> bool:
        """
        Release a distributed lock
        
        Args:
            key: Lock key
            
        Returns:
            True if lock released, False otherwise
        """
        if not self._redis_client:
            raise RuntimeError("Redis client not connected")
        
        lock_id = self._locks.get(key)
        if not lock_id:
            self.logger.warning(f"Attempted to release lock we don't own: {key}")
            return False
        
        try:
            # Use Lua script to ensure we only delete our own lock
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            result = await self._redis_client.eval(
                lua_script,
                1,
                key,
                lock_id
            )
            
            if result:
                del self._locks[key]
                self.logger.debug(
                    f"Released lock: {key}",
                    extra={"lock_id": lock_id}
                )
                return True
            else:
                self.logger.warning(
                    f"Lock was already released or expired: {key}",
                    extra={"lock_id": lock_id}
                )
                return False
                
        except Exception as e:
            self.logger.error(
                f"Error releasing lock: {key}",
                extra={"error": str(e), "lock_id": lock_id}
            )
            return False
    
    async def extend(self, key: str, ttl: int) -> bool:
        """
        Extend the TTL of a lock
        
        Args:
            key: Lock key
            ttl: New TTL in seconds
            
        Returns:
            True if lock extended, False otherwise
        """
        if not self._redis_client:
            raise RuntimeError("Redis client not connected")
        
        lock_id = self._locks.get(key)
        if not lock_id:
            self.logger.warning(f"Attempted to extend lock we don't own: {key}")
            return False
        
        try:
            # Use Lua script to ensure we only extend our own lock
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            
            result = await self._redis_client.eval(
                lua_script,
                1,
                key,
                lock_id,
                ttl
            )
            
            if result:
                self.logger.debug(
                    f"Extended lock: {key}",
                    extra={"lock_id": lock_id, "ttl": ttl}
                )
                return True
            else:
                self.logger.warning(
                    f"Failed to extend lock (not owner): {key}",
                    extra={"lock_id": lock_id}
                )
                return False
                
        except Exception as e:
            self.logger.error(
                f"Error extending lock: {key}",
                extra={"error": str(e), "lock_id": lock_id}
            )
            return False
    
    def get_lock_id(self, key: str) -> Optional[str]:
        """Get the lock ID for a key we own"""
        return self._locks.get(key)
    
    async def is_locked(self, key: str) -> bool:
        """Check if a key is locked (by anyone)"""
        if not self._redis_client:
            raise RuntimeError("Redis client not connected")
        
        try:
            result = await self._redis_client.exists(key)
            return bool(result)
        except Exception as e:
            self.logger.error(
                f"Error checking lock: {key}",
                extra={"error": str(e)}
            )
            return False