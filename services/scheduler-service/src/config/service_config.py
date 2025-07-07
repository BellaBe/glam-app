# services/scheduler-service/src/config/service_config.py
"""
Service configuration for Scheduler Service.

This configuration extends the shared BaseServiceConfig with
scheduler-specific settings.
"""

from typing import List, Optional
from shared.config import BaseServiceConfig


class ServiceConfig(BaseServiceConfig):
    """Configuration for Scheduler Service"""
    
    # Service identification
    SERVICE_NAME: str = "scheduler-service"
    SERVICE_VERSION: str = "1.0.0"
    API_PORT: int = 8008
    
    # Scheduler-specific configuration
    SCHEDULER_TIMEZONE: str = "UTC"
    SCHEDULER_JOB_STORE_URL: Optional[str] = None  # Will use main DB if not set
    SCHEDULER_MISFIRE_GRACE_TIME: int = 300  # 5 minutes
    SCHEDULER_MAX_INSTANCES: int = 3  # Max concurrent job instances
    SCHEDULER_EXECUTOR_POOL_SIZE: int = 10  # Thread pool size
    SCHEDULER_COALESCE: bool = True  # Coalesce missed jobs
    SCHEDULER_JOB_DEFAULTS_MAX_INSTANCES: int = 1  # Default max instances per job
    
    # Redis configuration for distributed locks
    REDIS_URL: str = "redis://localhost:6379/0"
    LOCK_TIMEOUT_SECONDS: int = 300  # 5 minutes
    LOCK_RETRY_DELAY: float = 0.1  # 100ms
    LOCK_MAX_RETRIES: int = 50  # Max retries for lock acquisition
    
    # Operational configuration
    MAX_SCHEDULE_LOOKAHEAD_DAYS: int = 365
    DEFAULT_MAX_RETRIES: int = 3
    DEFAULT_RETRY_DELAY: int = 300  # 5 minutes
    MAX_SCHEDULES_PER_CREATOR: int = 1000  # Rate limit per creator
    MAX_BULK_OPERATIONS: int = 100  # Max items in bulk operations
    
    # Command whitelist - allowed target commands
    ALLOWED_TARGET_COMMANDS: List[str] = [
        "cmd.notification.send.email",
        "cmd.notification.send.bulk",
        "cmd.notification.send.sms",
        "cmd.analytics.generate.report",
        "cmd.billing.process.invoices",
        "cmd.catalog.sync.products",
        "cmd.merchant.check.status",
    ]
    
    # Performance tuning
    SCHEDULE_CACHE_TTL: int = 300  # 5 minutes
    EXECUTION_HISTORY_RETENTION_DAYS: int = 30
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Use main database URL for job store if not specified
        if not self.SCHEDULER_JOB_STORE_URL:
            self.SCHEDULER_JOB_STORE_URL = self.DATABASE_URL.replace(
                "postgresql+asyncpg://", "postgresql://"
            )


def get_service_config() -> ServiceConfig:
    """Factory function to create service configuration"""
    return ServiceConfig()