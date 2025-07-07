# services/scheduler-service/src/exceptions.py
"""
Scheduler service exceptions using shared error classes.

All exceptions are re-exported from shared.errors for consistency
across the platform.
"""

from shared.errors.base import (
    NotFoundError,
    ConflictError,
    ValidationError,
    DomainError,
    RateLimitedError
)

# Re-export base exceptions for convenience
__all__ = [
    # Schedule errors
    'ScheduleNotFoundError',
    'ScheduleAlreadyExistsError',
    'InvalidScheduleError',
    'ScheduleLimitExceededError',
    
    # Execution errors
    'ExecutionNotFoundError',
    'ExecutionFailedError',
    
    # Lock errors
    'LockAcquisitionError',
    
    # From shared.errors.base
    'NotFoundError',
    'ConflictError',
    'ValidationError',
    'DomainError',
    'RateLimitedError'
]


# Schedule-specific errors
class ScheduleNotFoundError(NotFoundError):
    """Schedule not found"""
    
    def __init__(self, message: str, schedule_id: str):
        super().__init__(
            message,
            resource_type="schedule",
            resource_id=schedule_id
        )


class ScheduleAlreadyExistsError(ConflictError):
    """Schedule already exists"""
    
    def __init__(self, message: str, schedule_name: str):
        super().__init__(
            message,
            conflicting_resource="schedule",
            current_state=f"Schedule with name '{schedule_name}' already exists"
        )


class InvalidScheduleError(ValidationError):
    """Invalid schedule configuration"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message,
            field_errors=[{"field": field, "message": message}] if field else []
        )


class ScheduleLimitExceededError(RateLimitedError):
    """Schedule limit exceeded for creator"""
    
    def __init__(self, message: str, limit: int):
        super().__init__(
            message,
            retry_after_seconds=3600,  # Suggest retry after 1 hour
            limit=limit,
            window="per_creator"
        )


# Execution-specific errors
class ExecutionNotFoundError(NotFoundError):
    """Execution not found"""
    
    def __init__(self, message: str, execution_id: str):
        super().__init__(
            message,
            resource_type="execution",
            resource_id=execution_id
        )


class ExecutionFailedError(DomainError):
    """Execution failed"""
    
    def __init__(self, message: str, execution_id: str, error_type: Optional[str] = None):
        super().__init__(
            message=message,
            code="EXECUTION_FAILED",
            status=500,
            details={
                "execution_id": execution_id,
                "error_type": error_type
            }
        )


# Lock-specific errors
class LockAcquisitionError(DomainError):
    """Failed to acquire distributed lock"""
    
    def __init__(self, message: str, lock_key: str):
        super().__init__(
            message=message,
            code="LOCK_ACQUISITION_FAILED",
            status=409,  # Conflict
            details={"lock_key": lock_key}
        )