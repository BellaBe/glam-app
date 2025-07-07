# shared/events/scheduler/types.py
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

from shared.events.base import EventWrapper
from shared.events.context import EventContext


class ScheduleType(str, Enum):
    """Schedule type enumeration"""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"
    IMMEDIATE = "immediate"


class ExecutionStatus(str, Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class SchedulerCommands:
    """Scheduler command types"""
    SCHEDULE_CREATE = "cmd.scheduler.schedule.create"
    SCHEDULE_UPDATE = "cmd.scheduler.schedule.update"
    SCHEDULE_DELETE = "cmd.scheduler.schedule.delete"
    SCHEDULE_PAUSE = "cmd.scheduler.schedule.pause"
    SCHEDULE_RESUME = "cmd.scheduler.schedule.resume"
    SCHEDULE_TRIGGER = "cmd.scheduler.schedule.trigger"
    EXECUTE_IMMEDIATE = "cmd.scheduler.execute.immediate"


class SchedulerEvents:
    """Scheduler event types"""
    SCHEDULE_CREATED = "evt.scheduler.schedule.created"
    SCHEDULE_UPDATED = "evt.scheduler.schedule.updated"
    SCHEDULE_DELETED = "evt.scheduler.schedule.deleted"
    SCHEDULE_PAUSED = "evt.scheduler.schedule.paused"
    SCHEDULE_RESUMED = "evt.scheduler.schedule.resumed"
    SCHEDULE_TRIGGERED = "evt.scheduler.schedule.triggered"
    EXECUTION_STARTED = "evt.scheduler.execution.started"
    EXECUTION_COMPLETED = "evt.scheduler.execution.completed"
    EXECUTION_FAILED = "evt.scheduler.execution.failed"


# Command Payloads
class CreateScheduleCommandPayload(BaseModel):
    """Payload for creating a schedule"""
    name: str
    description: Optional[str] = None
    
    # Scheduling configuration
    schedule_type: ScheduleType
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    timezone: str = "UTC"
    
    # Execution configuration
    target_command: str
    command_payload: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    priority: int = Field(default=5, ge=1, le=10)
    max_retries: int = Field(default=3, ge=0)
    retry_delay_seconds: int = Field(default=300, ge=0)
    
    # Optional fields
    created_by: Optional[str] = None


class UpdateScheduleCommandPayload(BaseModel):
    """Payload for updating a schedule"""
    schedule_id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    
    # Scheduling configuration
    schedule_type: Optional[ScheduleType] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = None
    
    # Execution configuration
    target_command: Optional[str] = None
    command_payload: Optional[Dict[str, Any]] = None
    
    # Metadata
    tags: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    max_retries: Optional[int] = Field(None, ge=0)
    retry_delay_seconds: Optional[int] = Field(None, ge=0)
    
    # State
    is_active: Optional[bool] = None


class DeleteScheduleCommandPayload(BaseModel):
    """Payload for deleting a schedule"""
    schedule_id: UUID
    hard_delete: bool = False  # If true, delete permanently; if false, soft delete


class PauseScheduleCommandPayload(BaseModel):
    """Payload for pausing a schedule"""
    schedule_id: UUID
    reason: Optional[str] = None


class ResumeScheduleCommandPayload(BaseModel):
    """Payload for resuming a schedule"""
    schedule_id: UUID


class TriggerScheduleCommandPayload(BaseModel):
    """Payload for triggering a schedule immediately"""
    schedule_id: UUID
    override_payload: Optional[Dict[str, Any]] = None


class ExecuteImmediateCommandPayload(BaseModel):
    """Payload for immediate execution without scheduling"""
    target_command: str
    command_payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=5, ge=1, le=10)


# Event Payloads
class ScheduleCreatedEventPayload(BaseModel):
    """Payload for SCHEDULE_CREATED event"""
    schedule_id: UUID
    name: str
    schedule_type: ScheduleType
    target_command: str
    next_run_at: Optional[datetime]
    created_by: str
    created_at: datetime


class ScheduleUpdatedEventPayload(BaseModel):
    """Payload for SCHEDULE_UPDATED event"""
    schedule_id: UUID
    updated_fields: List[str]
    next_run_at: Optional[datetime]
    updated_by: str
    updated_at: datetime


class ScheduleDeletedEventPayload(BaseModel):
    """Payload for SCHEDULE_DELETED event"""
    schedule_id: UUID
    deleted_by: str
    deleted_at: datetime
    hard_delete: bool


class SchedulePausedEventPayload(BaseModel):
    """Payload for SCHEDULE_PAUSED event"""
    schedule_id: UUID
    reason: Optional[str]
    paused_by: str
    paused_at: datetime


class ScheduleResumedEventPayload(BaseModel):
    """Payload for SCHEDULE_RESUMED event"""
    schedule_id: UUID
    next_run_at: Optional[datetime]
    resumed_by: str
    resumed_at: datetime


class ScheduleTriggeredEventPayload(BaseModel):
    """Payload for SCHEDULE_TRIGGERED event"""
    schedule_id: UUID
    execution_id: UUID
    triggered_by: str
    triggered_at: datetime


class ExecutionStartedEventPayload(BaseModel):
    """Payload for EXECUTION_STARTED event"""
    execution_id: UUID
    schedule_id: UUID
    schedule_name: str
    target_command: str
    scheduled_for: datetime
    started_at: datetime
    attempt_number: int = 1


class ExecutionCompletedEventPayload(BaseModel):
    """Payload for EXECUTION_COMPLETED event"""
    execution_id: UUID
    schedule_id: UUID
    status: ExecutionStatus
    duration_ms: int
    completed_at: datetime
    next_run_at: Optional[datetime]


class ExecutionFailedEventPayload(BaseModel):
    """Payload for EXECUTION_FAILED event"""
    execution_id: UUID
    schedule_id: UUID
    error_message: str
    error_type: Optional[str]
    will_retry: bool
    retry_at: Optional[datetime]
    attempt_number: int
    failed_at: datetime