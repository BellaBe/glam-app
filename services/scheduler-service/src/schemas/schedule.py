# services/scheduler-service/src/schemas/schedule.py
"""Schedule-related schemas"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum
import re
from croniter import croniter

from .base import BaseSchema


class ScheduleType(str, Enum):
    """Schedule type enumeration"""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"
    IMMEDIATE = "immediate"


class ScheduleStatus(str, Enum):
    """Schedule status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class ScheduleCreate(BaseModel):
    """Schema for creating a schedule"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Scheduling configuration
    schedule_type: ScheduleType
    cron_expression: Optional[str] = Field(None, max_length=255)
    interval_seconds: Optional[int] = Field(None, gt=0, le=31536000)  # Max 1 year
    scheduled_at: Optional[datetime] = None
    timezone: str = Field(default="UTC", max_length=50)
    
    # Execution configuration
    target_command: str = Field(..., min_length=1, max_length=255)
    command_payload: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    tags: List[str] = Field(default_factory=list, max_items=20)
    priority: int = Field(default=5, ge=1, le=10)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=300, ge=0, le=3600)
    
    @field_validator('cron_expression')
    def validate_cron(cls, v: Optional[str], values) -> Optional[str]:
        if v and values.data.get('schedule_type') == ScheduleType.CRON:
            if not croniter.is_valid(v):
                raise ValueError('Invalid cron expression')
        return v
    
    @field_validator('scheduled_at')
    def validate_scheduled_at(cls, v: Optional[datetime], values) -> Optional[datetime]:
        if values.data.get('schedule_type') == ScheduleType.ONE_TIME and not v:
            raise ValueError('scheduled_at is required for ONE_TIME schedules')
        if v and v < datetime.utcnow():
            raise ValueError('scheduled_at must be in the future')
        return v
    
    @field_validator('interval_seconds')
    def validate_interval(cls, v: Optional[int], values) -> Optional[int]:
        if values.data.get('schedule_type') == ScheduleType.INTERVAL and not v:
            raise ValueError('interval_seconds is required for INTERVAL schedules')
        return v
    
    @field_validator('target_command')
    def validate_command_format(cls, v: str) -> str:
        # Ensure command follows pattern: cmd.domain.action
        pattern = r'^cmd\.[a-z]+\.[a-z.]+$'
        if not re.match(pattern, v):
            raise ValueError('Invalid command format. Must be cmd.domain.action')
        return v


class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Scheduling configuration
    schedule_type: Optional[ScheduleType] = None
    cron_expression: Optional[str] = Field(None, max_length=255)
    interval_seconds: Optional[int] = Field(None, gt=0, le=31536000)
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = Field(None, max_length=50)
    
    # Execution configuration
    target_command: Optional[str] = Field(None, min_length=1, max_length=255)
    command_payload: Optional[Dict[str, Any]] = None
    
    # Metadata
    tags: Optional[List[str]] = Field(None, max_items=20)
    priority: Optional[int] = Field(None, ge=1, le=10)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay_seconds: Optional[int] = Field(None, ge=0, le=3600)
    
    # State
    is_active: Optional[bool] = None


class ScheduleResponse(BaseSchema):
    """Response schema for schedule"""
    id: UUID
    name: str
    description: Optional[str]
    
    # Scheduling
    schedule_type: ScheduleType
    cron_expression: Optional[str]
    interval_seconds: Optional[int]
    scheduled_at: Optional[datetime]
    timezone: str
    
    # Execution
    target_command: str
    
    # State
    status: ScheduleStatus
    is_active: bool
    is_paused: bool
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    
    # Stats
    run_count: int
    success_count: int
    failure_count: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class ScheduleDetailResponse(ScheduleResponse):
    """Detailed response schema for schedule"""
    command_payload: Dict[str, Any]
    tags: List[str]
    priority: int
    max_retries: int
    retry_delay_seconds: int
    
    # Additional details
    pause_reason: Optional[str]
    created_by: str
    updated_by: Optional[str]
    job_id: Optional[str]
    correlation_id: Optional[str]


class ScheduleListResponse(BaseSchema):
    """Response for schedule list"""
    schedules: List[ScheduleResponse]
    total: int
    page: int
    limit: int


class ScheduleBulkCreate(BaseModel):
    """Schema for bulk schedule creation"""
    schedules: List[ScheduleCreate] = Field(..., max_items=100)


class ScheduleBulkOperation(BaseModel):
    """Schema for bulk operations on schedules"""
    schedule_ids: List[UUID] = Field(..., max_items=100)
    operation: str = Field(..., regex="^(pause|resume|delete)$")
    reason: Optional[str] = Field(None, max_length=500)  # For pause operation


class ScheduleTrigger(BaseModel):
    """Schema for triggering a schedule"""
    override_payload: Optional[Dict[str, Any]] = None