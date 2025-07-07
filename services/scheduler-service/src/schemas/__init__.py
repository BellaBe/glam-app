# services/scheduler-service/src/schemas/__init__.py
from .schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleDetailResponse,
    ScheduleListResponse,
    ScheduleBulkCreate,
    ScheduleBulkOperation,
    ScheduleTrigger
)
from .execution import (
    ExecutionResponse,
    ExecutionDetailResponse,
    ExecutionListResponse,
    ExecutionStats
)

__all__ = [
    # Schedule schemas
    'ScheduleCreate',
    'ScheduleUpdate',
    'ScheduleResponse',
    'ScheduleDetailResponse',
    'ScheduleListResponse',
    'ScheduleBulkCreate',
    'ScheduleBulkOperation',
    'ScheduleTrigger',
    # Execution schemas
    'ExecutionResponse',
    'ExecutionDetailResponse',
    'ExecutionListResponse',
    'ExecutionStats'
]