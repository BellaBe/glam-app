
# services/scheduler-service/src/mappers/schedule_mapper.py
"""Mapper for schedule schemas and models"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from shared.api.correlation import get_correlation_context
from ..models.schedule import Schedule, ScheduleType, ScheduleStatus
from ..schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleDetailResponse
)
from .base import BaseMapper


class ScheduleMapper(BaseMapper[
    Schedule,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse
]):
    """Maps between schedule schemas and models"""
    
    def create_to_model(
        self,
        create_schema: ScheduleCreate,
        *,
        created_by: str,
        correlation_id: Optional[str] = None
    ) -> Schedule:
        """Convert ScheduleCreate schema to Schedule model"""
        
        # Get correlation ID from context if not provided
        if not correlation_id:
            ctx = get_correlation_context()
            correlation_id = ctx.correlation_id if ctx else None
        
        # Create model instance
        schedule = Schedule(
            name=create_schema.name,
            description=create_schema.description,
            schedule_type=create_schema.schedule_type,
            cron_expression=create_schema.cron_expression,
            interval_seconds=create_schema.interval_seconds,
            scheduled_at=create_schema.scheduled_at,
            timezone=create_schema.timezone,
            target_command=create_schema.target_command,
            command_payload=create_schema.command_payload,
            tags=create_schema.tags,
            priority=create_schema.priority,
            max_retries=create_schema.max_retries,
            retry_delay_seconds=create_schema.retry_delay_seconds,
            created_by=created_by,
            correlation_id=correlation_id,
            status=ScheduleStatus.ACTIVE,
            is_active=True,
            is_paused=False
        )
        
        return schedule
    
    def update_to_model(
        self,
        model: Schedule,
        update_schema: ScheduleUpdate,
        *,
        updated_by: str
    ) -> Schedule:
        """Apply update schema to model"""
        
        # Track updated fields for event
        updated_fields = []
        
        # Update basic fields
        if update_schema.name is not None:
            model.name = update_schema.name
            updated_fields.append("name")
        
        if update_schema.description is not None:
            model.description = update_schema.description
            updated_fields.append("description")
        
        # Update scheduling configuration
        if update_schema.schedule_type is not None:
            model.schedule_type = update_schema.schedule_type
            updated_fields.append("schedule_type")
        
        if update_schema.cron_expression is not None:
            model.cron_expression = update_schema.cron_expression
            updated_fields.append("cron_expression")
        
        if update_schema.interval_seconds is not None:
            model.interval_seconds = update_schema.interval_seconds
            updated_fields.append("interval_seconds")
        
        if update_schema.scheduled_at is not None:
            model.scheduled_at = update_schema.scheduled_at
            updated_fields.append("scheduled_at")
        
        if update_schema.timezone is not None:
            model.timezone = update_schema.timezone
            updated_fields.append("timezone")
        
        # Update execution configuration
        if update_schema.target_command is not None:
            model.target_command = update_schema.target_command
            updated_fields.append("target_command")
        
        if update_schema.command_payload is not None:
            model.command_payload = update_schema.command_payload
            updated_fields.append("command_payload")
        
        # Update metadata
        if update_schema.tags is not None:
            model.tags = update_schema.tags
            updated_fields.append("tags")
        
        if update_schema.priority is not None:
            model.priority = update_schema.priority
            updated_fields.append("priority")
        
        if update_schema.max_retries is not None:
            model.max_retries = update_schema.max_retries
            updated_fields.append("max_retries")
        
        if update_schema.retry_delay_seconds is not None:
            model.retry_delay_seconds = update_schema.retry_delay_seconds
            updated_fields.append("retry_delay_seconds")
        
        # Update state
        if update_schema.is_active is not None:
            model.is_active = update_schema.is_active
            updated_fields.append("is_active")
        
        # Update tracking
        model.updated_by = updated_by
        model.updated_at = datetime.utcnow()
        
        # Store updated fields for event publishing
        model._updated_fields = updated_fields
        
        return model
    
    def model_to_response(self, model: Schedule) -> ScheduleResponse:
        """Convert model to response schema"""
        return ScheduleResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            schedule_type=model.schedule_type,
            cron_expression=model.cron_expression,
            interval_seconds=model.interval_seconds,
            scheduled_at=model.scheduled_at,
            timezone=model.timezone,
            target_command=model.target_command,
            status=model.status,
            is_active=model.is_active,
            is_paused=model.is_paused,
            next_run_at=model.next_run_at,
            last_run_at=model.last_run_at,
            run_count=model.run_count,
            success_count=model.success_count,
            failure_count=model.failure_count,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def model_to_detail_response(self, model: Schedule) -> ScheduleDetailResponse:
        """Convert model to detailed response schema"""
        return ScheduleDetailResponse(
            id=model.id,
            name=model.name,
            description=model.description,
            schedule_type=model.schedule_type,
            cron_expression=model.cron_expression,
            interval_seconds=model.interval_seconds,
            scheduled_at=model.scheduled_at,
            timezone=model.timezone,
            target_command=model.target_command,
            command_payload=model.command_payload,
            tags=model.tags,
            priority=model.priority,
            max_retries=model.max_retries,
            retry_delay_seconds=model.retry_delay_seconds,
            status=model.status,
            is_active=model.is_active,
            is_paused=model.is_paused,
            pause_reason=model.pause_reason,
            next_run_at=model.next_run_at,
            last_run_at=model.last_run_at,
            run_count=model.run_count,
            success_count=model.success_count,
            failure_count=model.failure_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by,
            job_id=model.job_id,
            correlation_id=model.correlation_id
        )
