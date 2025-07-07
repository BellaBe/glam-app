# services/scheduler-service/src/schemas/execution.py
"""Execution-related schemas"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

from .base import BaseSchema


class ExecutionStatus(str, Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ExecutionResponse(BaseSchema):
    """Response schema for execution"""
    id: UUID
    schedule_id: UUID
    
    # Timing
    scheduled_for: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    # Status
    status: ExecutionStatus
    attempt_number: int
    
    # Performance
    duration_ms: Optional[int]
    
    # Error info (if failed)
    error_message: Optional[str]
    error_type: Optional[str]


class ExecutionDetailResponse(ExecutionResponse):
    """Detailed response schema for execution"""
    # Command details
    command_sent: Optional[str]
    command_payload: Optional[Dict[str, Any]]
    
    # Response details
    response_event: Optional[str]
    response_payload: Optional[Dict[str, Any]]
    
    # Tracking
    correlation_id: str
    lock_id: Optional[str]


class ExecutionListResponse(BaseSchema):
    """Response for execution list"""
    executions: List[ExecutionResponse]
    total: int
    page: int
    limit: int


class ExecutionStats(BaseSchema):
    """Execution statistics for a schedule"""
    schedule_id: UUID
    total_executions: int
    successful_executions: int
    failed_executions: int
    skipped_executions: int
    average_duration_ms: Optional[float]
    min_duration_ms: Optional[int]
    max_duration_ms: Optional[int]
    last_execution_at: Optional[datetime]
    next_execution_at: Optional[datetime]
    
    # Time period stats
    executions_last_hour: int
    executions_last_24h: int
    executions_last_7d: int
    
    # Success rate
    success_rate: float = Field(ge=0, le=1)
    
    # Failure analysis
    most_common_error: Optional[str]
    consecutive_failures: int