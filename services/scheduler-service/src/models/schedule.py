
# services/scheduler-service/src/models/schedule.py
"""Schedule model for storing schedule configurations"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, JSON, 
    UniqueConstraint, Index, Text, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from shared.database.base import Base
from shared.database.mixins import TimestampMixin


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
    COMPLETED = "completed"  # For one-time schedules
    FAILED = "failed"
    DELETED = "deleted"  # Soft delete


class Schedule(Base, TimestampMixin):
    """Schedule model for storing job schedules"""
    
    __tablename__ = "schedules"
    __table_args__ = (
        UniqueConstraint('name', 'created_by', name='uq_schedule_name_creator'),
        Index('ix_schedule_next_run', 'next_run_at', 'status'),
        Index('ix_schedule_type_status', 'schedule_type', 'status'),
        Index('ix_schedule_created_by', 'created_by'),
        Index('ix_schedule_tags', 'tags', postgresql_using='gin'),
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Basic information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Scheduling configuration
    schedule_type = Column(
        SQLEnum(ScheduleType, native_enum=False),
        nullable=False,
        index=True
    )
    cron_expression = Column(String(255), nullable=True)  # For CRON type
    interval_seconds = Column(Integer, nullable=True)  # For INTERVAL type
    scheduled_at = Column(DateTime(timezone=True), nullable=True)  # For ONE_TIME type
    timezone = Column(String(50), nullable=False, default="UTC")
    
    # Execution configuration
    target_command = Column(String(255), nullable=False, index=True)
    command_payload = Column(JSON, nullable=False, default=dict)
    
    # Metadata
    tags = Column(JSON, nullable=False, default=list)  # List of tags
    priority = Column(Integer, nullable=False, default=5)  # 1-10
    max_retries = Column(Integer, nullable=False, default=3)
    retry_delay_seconds = Column(Integer, nullable=False, default=300)
    
    # State
    status = Column(
        SQLEnum(ScheduleStatus, native_enum=False),
        nullable=False,
        default=ScheduleStatus.ACTIVE,
        index=True
    )
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_paused = Column(Boolean, nullable=False, default=False)
    pause_reason = Column(Text, nullable=True)
    
    # Execution tracking
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    run_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    
    # APScheduler integration
    job_id = Column(String(255), nullable=True, unique=True, index=True)
    
    # Tracking
    created_by = Column(String(255), nullable=False)  # Service or user
    updated_by = Column(String(255), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    deleted_by = Column(String(255), nullable=True)
    
    # Correlation for tracing
    correlation_id = Column(String(255), nullable=True, index=True)
    
    def __repr__(self) -> str:
        return f"<Schedule(id={self.id}, name={self.name}, type={self.schedule_type})>"