# services/webhook-service/src/services/circuit_breaker_service.py
"""Circuit breaker for downstream services."""

from typing import Optional, Dict
from datetime import datetime, timedelta
from enum import Enum
import json
import redis.asyncio as redis

from shared.utils.logger import ServiceLogger


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"      # Failing, reject requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class CircuitBreakerService:
    """
    Circuit breaker implementation using Redis for state storage.
    
    Protects downstream services from cascading failures.
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        window_seconds: int = 30,
        logger: Optional[ServiceLogger] = None
    ):
        self.redis = redis_client
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.window_seconds = window_seconds
        self.logger = logger or ServiceLogger(__name__)
        self.key_prefix = "webhook:circuit:"
    
    async def can_proceed(self, subject: str) -> bool:
        """Check if request can proceed for given subject"""
        state = await self._get_state(subject)
        
        if state["state"] == CircuitState.CLOSED:
            return True
        
        elif state["state"] == CircuitState.OPEN:
            # Check if timeout has passed
            if datetime.utcnow() > state["open_until"]:
                # Move to half-open
                await self._set_state(subject, CircuitState.HALF_OPEN)
                return True
            return False
        
        elif state["state"] == CircuitState.HALF_OPEN:
            # Allow one request through to test
            return True
        
        return False
    
    async def record_success(self, subject: str):
        """Record successful request"""
        state = await self._get_state(subject)
        
        if state["state"] == CircuitState.HALF_OPEN:
            # Recovery successful, close circuit
            await self._set_state(subject, CircuitState.CLOSED)
            await self._reset_failures(subject)
            
            self.logger.info(
                f"Circuit closed for {subject} after successful recovery"
            )
    
    async def record_failure(self, subject: str):
        """Record failed request"""
        state = await self._get_state(subject)
        
        if state["state"] == CircuitState.HALF_OPEN:
            # Still failing, reopen
            await self._set_state(subject, CircuitState.OPEN)
            self.logger.warning(
                f"Circuit reopened for {subject} after half-open failure"
            )
            return
        
        # Increment failure count
        failures = await self._increment_failures(subject)
        
        if failures >= self.failure_threshold:
            await self._set_state(subject, CircuitState.OPEN)
            self.logger.warning(
                f"Circuit opened for {subject} after {failures} failures"
            )
    
    async def _get_state(self, subject: str) -> Dict:
        """Get current circuit state"""
        key = f"{self.key_prefix}state:{subject}"
        
        try:
            data = await self.redis.get(key)
            if data:
                state_data = json.loads(data)
                # Parse datetime
                if "open_until" in state_data:
                    state_data["open_until"] = datetime.fromisoformat(
                        state_data["open_until"]
                    )
                return state_data
        except Exception as e:
            self.logger.error(f"Failed to get circuit state: {e}")
        
        # Default state
        return {
            "state": CircuitState.CLOSED,
            "failures": 0,
            "last_failure": None,
            "open_until": None
        }
    
    async def _set_state(
        self, 
        subject: str, 
        state: CircuitState
    ):
        """Set circuit state"""
        key = f"{self.key_prefix}state:{subject}"
        
        state_data = {
            "state": state,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if state == CircuitState.OPEN:
            state_data["open_until"] = (
                datetime.utcnow() + timedelta(seconds=self.timeout_seconds)
            ).isoformat()
        
        try:
            await self.redis.setex(
                key,
                self.timeout_seconds * 2,  # Expire after 2x timeout
                json.dumps(state_data)
            )
        except Exception as e:
            self.logger.error(f"Failed to set circuit state: {e}")
    
    async def _increment_failures(self, subject: str) -> int:
        """Increment failure count within window"""
        key = f"{self.key_prefix}failures:{subject}"
        
        try:
            # Use Redis increment with expiry
            failures = await self.redis.incr(key)
            
            # Set expiry on first failure
            if failures == 1:
                await self.redis.expire(key, self.window_seconds)
            
            return failures
        except Exception as e:
            self.logger.error(f"Failed to increment failures: {e}")
            return 0
    
    async def _reset_failures(self, subject: str):
        """Reset failure count"""
        key = f"{self.key_prefix}failures:{subject}"
        
        try:
            await self.redis.delete(key)
        except Exception as e:
            self.logger.error(f"Failed to reset failures: {e}")
    
    async def get_status(self, subject: str) -> Dict:
        """Get detailed circuit status (for monitoring)"""
        state = await self._get_state(subject)
        
        # Get failure count
        failures_key = f"{self.key_prefix}failures:{subject}"
        try:
            failures = await self.redis.get(failures_key)
            state["current_failures"] = int(failures) if failures else 0
        except:
            state["current_failures"] = 0
        
        return state