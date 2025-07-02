from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..models.entities import NotificationRateLimit
import re

class RateLimiter:
    """Email rate limiting implementation"""
    
    def __init__(self, config: dict):
        self.config = config
        self.default_rate_limit = self._parse_rate_limit(config.get('rate_limit', '10/min'))
        self.burst_limit = config.get('burst_limit', 20)
        self.daily_limit = config.get('daily_limit', 1000)
    
    async def check_rate_limit(
        self, 
        session: AsyncSession,
        recipient_email: str,
        notification_type: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Check if email can be sent within rate limits"""
        
        # Check burst limit (last minute)
        burst_window_start = datetime.utcnow() - timedelta(minutes=1)
        burst_count = await self._get_send_count(
            session, recipient_email, notification_type, burst_window_start
        )
        
        if burst_count >= self.burst_limit:
            return False, f"Burst limit exceeded: {burst_count}/{self.burst_limit} in last minute"
        
        # Check rate limit
        rate_count, rate_window = self.default_rate_limit
        window_start = datetime.utcnow() - rate_window
        current_count = await self._get_send_count(
            session, recipient_email, notification_type, window_start
        )
        
        if current_count >= rate_count:
            return False, f"Rate limit exceeded: {current_count}/{rate_count} in {rate_window}"
        
        # Check daily limit
        daily_start = datetime.utcnow() - timedelta(days=1)
        daily_count = await self._get_send_count(
            session, recipient_email, notification_type, daily_start
        )
        
        if daily_count >= self.daily_limit:
            return False, f"Daily limit exceeded: {daily_count}/{self.daily_limit}"
        
        return True, None
    
    async def record_send(
        self,
        session: AsyncSession,
        recipient_email: str,
        notification_type: Optional[str] = None
    ):
        """Record email send for rate limiting"""
        window_start = datetime.utcnow()
        window_end = window_start + timedelta(hours=1)
        
        # Check if record exists for current window
        stmt = select(NotificationRateLimit).where(
            and_(
                NotificationRateLimit.recipient_email == recipient_email,
                NotificationRateLimit.notification_type == notification_type,
                NotificationRateLimit.window_start <= window_start,
                NotificationRateLimit.window_end > window_start
            )
        )
        
        result = await session.execute(stmt)
        rate_limit = result.scalar_one_or_none()
        
        if rate_limit:
            rate_limit.send_count += 1
        else:
            rate_limit = NotificationRateLimit(
                recipient_email=recipient_email,
                notification_type=notification_type,
                send_count=1,
                window_start=window_start,
                window_end=window_end
            )
            session.add(rate_limit)
        
        await session.commit()
    
    async def _get_send_count(
        self,
        session: AsyncSession,
        recipient_email: str,
        notification_type: Optional[str],
        since: datetime
    ) -> int:
        """Get send count since timestamp"""
        stmt = select(NotificationRateLimit).where(
            and_(
                NotificationRateLimit.recipient_email == recipient_email,
                NotificationRateLimit.notification_type == notification_type,
                NotificationRateLimit.window_start >= since
            )
        )
        
        result = await session.execute(stmt)
        rate_limits = result.scalars().all()
        
        return sum(rl.send_count for rl in rate_limits)
    
    def _parse_rate_limit(self, rate_str: str) -> Tuple[int, timedelta]:
        """Parse rate limit string (e.g., '10/min', '100/hour')"""
        match = re.match(r'(\d+)/(\w+)', rate_str)
        if not match:
            raise ValueError(f"Invalid rate limit format: {rate_str}")
        
        count = int(match.group(1))
        unit = match.group(2)
        
        unit_map = {
            'sec': timedelta(seconds=1),
            'min': timedelta(minutes=1),
            'hour': timedelta(hours=1),
            'day': timedelta(days=1)
        }
        
        if unit not in unit_map:
            raise ValueError(f"Invalid rate limit unit: {unit}")
        
        return count, unit_map[unit]