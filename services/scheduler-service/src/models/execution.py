# services/scheduler-service/src/models/execution.py
"""Execution model for tracking schedule executions"""

from sqlalchemy import (
    Column, String, Integer, DateTime, JSON, ForeignKey,
    Index, Text, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from shared.database.base import Base


class ExecutionStatus(str, Enum):
    """Execution status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class ScheduleExecution(Base):
    """Execution records for schedule runs"""
    
    __tablename__ = "schedule_executions"
    __table_args__ = (
        Index('ix_execution_schedule_status', 'schedule_id', 'status'),
        Index('ix_execution_scheduled_for', 'scheduled_for'),
        Index('ix_execution_started_at', 'started_at'),
        Index('ix_execution_correlation', 'correlation_id'),
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Reference to schedule
    schedule_id = Column(
        UUID(as_uuid=True),
        ForeignKey('schedules.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Timing
    scheduled_for = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(
        SQLEnum(ExecutionStatus, native_enum=False),
        nullable=False,
        default=ExecutionStatus.PENDING,
        index=True
    )
    attempt_number = Column(Integer, nullable=False, default=1)
    
    # Command information
    command_sent = Column(String(255), nullable=True)  # Actual command sent
    command_payload = Column(JSON, nullable=True)  # Payload sent
    
    # Response/Result
    response_event = Column(String(255), nullable=True)  # Response event type
    response_payload = Column(JSON, nullable=True)  # Response data
    error_message = Column(Text, nullable=True)
    error_type = Column(String(255), nullable=True)
    
    # Performance
    duration_ms = Column(Integer, nullable=True)  # Execution duration
    
    # Tracking
    correlation_id = Column(String(255), nullable=False)
    lock_id = Column(String(255), nullable=True)  # Distributed lock ID
    
    # Relationship
    schedule = relationship("Schedule", backref="executions")
    
    def __repr__(self) -> str:
        return f"<ScheduleExecution(id={self.id}, schedule_id={self.schedule_id}, status={self.status})>"