# File: services/connector-service/src/services/rate_limit_service.py

"""Rate limiting service for API calls."""

from typing import Optional
from datetime import datetime, timedelta, timezone
import asyncio
from contextlib import asynccontextmanager

from shared.utils.logger import ServiceLogger
from ..repositories.rate_limit_repository import RateLimitRepository
from ..exceptions import RateLimitExceededError


class RateLimitService:
    """Manages API rate limiting."""
    
    def __init__(
        self,
        repository: RateLimitRepository,
        logger: ServiceLogger,
        default_limit: int = 40,
        window_seconds: int = 60
    ):
        self.repository = repository
        self.logger = logger
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._locks = {}  # Store-endpoint locks for concurrent access
    
    def _get_lock_key(self, store_id: str, endpoint: str) -> str:
        """Get lock key for store-endpoint combination."""
        return f"{store_id}:{endpoint}"
    
    def _get_lock(self, store_id: str, endpoint: str) -> asyncio.Lock:
        """Get or create lock for store-endpoint."""
        key = self._get_lock_key(store_id, endpoint)
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
    
    async def check_rate_limit(
        self,
        store_id: str,
        endpoint: str,
        current_used: Optional[int] = None
    ) -> bool:
        """Check if rate limit allows request."""
        async with self._get_lock(store_id, endpoint):
            now = datetime.now(timezone.utc)
            
            # Get or create rate limit state
            state = await self.repository.get_or_create(
                store_id=store_id,
                endpoint=endpoint,
                reset_at=now + timedelta(seconds=self.window_seconds)
            )
            
            # Check if window has expired
            if now >= state.reset_at:
                await self.repository.reset_calls(
                    store_id=store_id,
                    endpoint=endpoint,
                    reset_at=now + timedelta(seconds=self.window_seconds)
                )
                state.calls_made = 0
            
            # Update with actual usage if provided
            if current_used is not None:
                state.calls_made = current_used
            
            # Check limit
            if state.calls_made >= state.calls_limit:
                seconds_until_reset = (state.reset_at - now).total_seconds()
                raise RateLimitExceededError(
                    store_id=store_id,
                    retry_after=int(seconds_until_reset)
                )
            
            return True
    
    @asynccontextmanager
    async def rate_limit_context(self, store_id: str, endpoint: str):
        """Context manager for rate-limited operations."""
        # Check before
        await self.check_rate_limit(store_id, endpoint)
        
        try:
            yield
            
            # Increment after successful call
            await self.repository.increment_calls(
                store_id=store_id,
                endpoint=endpoint,
                current_time=datetime.now(timezone.utc)
            )
            
        except RateLimitExceededError:
            # Re-raise rate limit errors
            raise
        except Exception as e:
            # Don't increment on other errors
            self.logger.error(
                f"Error during rate-limited operation: {str(e)}",
                extra={"store_id": store_id, "endpoint": endpoint}
            )
            raise
    
    async def update_from_headers(
        self,
        store_id: str,
        endpoint: str,
        current_used: int,
        limit: int
    ) -> None:
        """Update rate limit state from API response headers."""
        async with self._get_lock(store_id, endpoint):
            now = datetime.now(timezone.utc)
            
            state = await self.repository.get_or_create(
                store_id=store_id,
                endpoint=endpoint,
                reset_at=now + timedelta(seconds=self.window_seconds)
            )
            
            # Update with actual values from API
            state.calls_made = current_used
            state.calls_limit = limit
            state.last_call_at = now
            
            await self.repository.update(state)
            
            # Log warning if approaching limit
            usage_percent = (current_used / limit) * 100
            if usage_percent >= 80:
                self.logger.warning(
                    f"High rate limit usage: {usage_percent:.1f}%",
                    extra={
                        "store_id": store_id,
                        "endpoint": endpoint,
                        "usage": f"{current_used}/{limit}"
                    }
                )