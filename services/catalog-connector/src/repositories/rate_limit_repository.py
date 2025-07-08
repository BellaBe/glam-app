# File: services/connector-service/src/repositories/rate_limit_repository.py

"""Repository for rate limit states."""

from typing import Optional
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from shared.database import Repository
from ..models.rate_limit import RateLimitState


class RateLimitRepository(Repository[RateLimitState]):
    """Repository for rate limit operations."""
    
    async def get_or_create(
        self,
        store_id: str,
        endpoint: str,
        reset_at: datetime
    ) -> RateLimitState:
        """Get or create rate limit state."""
        async with self.session_factory() as session:
            # Try to get existing
            result = await session.execute(
                select(self.model).where(
                    self.model.store_id == store_id,
                    self.model.endpoint == endpoint
                )
            )
            state = result.scalars().first()
            
            if state:
                return state
            
            # Create new
            state = self.model(
                store_id=store_id,
                endpoint=endpoint,
                calls_made=0,
                calls_limit=40,
                reset_at=reset_at
            )
            session.add(state)
            await session.commit()
            await session.refresh(state)
            return state
    
    async def increment_calls(
        self,
        store_id: str,
        endpoint: str,
        current_time: datetime
    ) -> RateLimitState:
        """Increment call count and update last call time."""
        async with self.session_factory() as session:
            # Use upsert to handle concurrent updates
            stmt = insert(self.model).values(
                store_id=store_id,
                endpoint=endpoint,
                calls_made=1,
                calls_limit=40,
                reset_at=current_time,
                last_call_at=current_time
            )
            
            stmt = stmt.on_conflict_do_update(
                constraint="uq_store_endpoint",
                set_=dict(
                    calls_made=self.model.calls_made + 1,
                    last_call_at=current_time
                )
            )
            
            await session.execute(stmt)
            await session.commit()
            
            # Fetch updated state
            result = await session.execute(
                select(self.model).where(
                    self.model.store_id == store_id,
                    self.model.endpoint == endpoint
                )
            )
            return result.scalars().first()
    
    async def reset_calls(
        self,
        store_id: str,
        endpoint: str,
        reset_at: datetime
    ) -> None:
        """Reset call count for new period."""
        async with self.session_factory() as session:
            await session.execute(
                update(self.model)
                .where(
                    self.model.store_id == store_id,
                    self.model.endpoint == endpoint
                )
                .values(
                    calls_made=0,
                    reset_at=reset_at
                )
            )
            await session.commit()