# services/notification_service/src/services/in_memory_rate_limit_service.py
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Tuple

from shared.utils.logger import ServiceLogger

@dataclass
class RateLimitConfig:
    burst_limit: int = 10
    burst_window_seconds: int = 60
    hourly_limit: int = 20
    daily_limit: int = 100

def _now() -> datetime:
    return datetime.now(timezone.utc)

class InMemoryRateLimitService:
    """
    **Process-local** token-bucket limiter.
    ✔ zero infrastructure
    ✘ does NOT synchronise across multiple replicas or restarts.
    """

    def __init__(self, logger: ServiceLogger):
        self.logger = logger
        # dict[(recipient, type)] -> list[timestamps]
        self._events: Dict[Tuple[str, str], list[datetime]] = defaultdict(list)

    # public -----------------------------------------------------------------
    async def check_and_increment(self, recipient: str, notification_type: str) -> bool:
        cfg = RateLimitConfig()
        now = _now()
        events = self._events[(recipient, notification_type)]

        # purge old timestamps ------------------------------------------------
        events[:] = [ts for ts in events
                     if now - ts < timedelta(days=1)]  # keep last 24 h

        # helpers -------------------------------------------------------------
        def count_since(delta: timedelta) -> int:
            cutoff = now - delta
            return sum(ts >= cutoff for ts in events)

        if count_since(timedelta(seconds=cfg.burst_window_seconds)) >= cfg.burst_limit:
            return False
        if count_since(timedelta(hours=1)) >= cfg.hourly_limit:
            return False
        if len(events) >= cfg.daily_limit:
            return False

        events.append(now)
        return True
