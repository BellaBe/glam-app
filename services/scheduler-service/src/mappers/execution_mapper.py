# services/scheduler-service/src/mappers/execution_mapper.py
"""Mapper for execution schemas and models"""

from typing import Dict, Any, Optional
from uuid import UUID

from ..models.execution import ScheduleExecution, ExecutionStatus
from ..schemas.execution import (
    ExecutionResponse,
    ExecutionDetailResponse,
    ExecutionStats
)
from .base import BaseMapper


class ExecutionMapper:
    """Maps between execution models and schemas"""
    
    def model_to_response(self, model: ScheduleExecution) -> ExecutionResponse:
        """Convert model to response schema"""
        return ExecutionResponse(
            id=model.id,
            schedule_id=model.schedule_id,
            scheduled_for=model.scheduled_for,
            started_at=model.started_at,
            completed_at=model.completed_at,
            status=model.status,
            attempt_number=model.attempt_number,
            duration_ms=model.duration_ms,
            error_message=model.error_message,
            error_type=model.error_type
        )
    
    def model_to_detail_response(self, model: ScheduleExecution) -> ExecutionDetailResponse:
        """Convert model to detailed response schema"""
        return ExecutionDetailResponse(
            id=model.id,
            schedule_id=model.schedule_id,
            scheduled_for=model.scheduled_for,
            started_at=model.started_at,
            completed_at=model.completed_at,
            status=model.status,
            attempt_number=model.attempt_number,
            duration_ms=model.duration_ms,
            error_message=model.error_message,
            error_type=model.error_type,
            command_sent=model.command_sent,
            command_payload=model.command_payload,
            response_event=model.response_event,
            response_payload=model.response_payload,
            correlation_id=model.correlation_id,
            lock_id=model.lock_id
        )
    
    def stats_to_response(
        self,
        stats: Dict[str, Any],
        schedule_id: UUID,
        next_run_at: Optional[datetime] = None
    ) -> ExecutionStats:
        """Convert stats dictionary to response schema"""
        
        # Calculate time period stats (would need to be implemented in repository)
        executions_last_hour = stats.get('executions_last_hour', 0)
        executions_last_24h = stats.get('executions_last_24h', 0)
        executions_last_7d = stats.get('executions_last_7d', 0)
        
        # Get most common error (would need to be implemented)
        most_common_error = stats.get('most_common_error')
        
        return ExecutionStats(
            schedule_id=schedule_id,
            total_executions=stats['total_executions'],
            successful_executions=stats['successful_executions'],
            failed_executions=stats['failed_executions'],
            skipped_executions=stats['skipped_executions'],
            average_duration_ms=stats['average_duration_ms'],
            min_duration_ms=stats['min_duration_ms'],
            max_duration_ms=stats['max_duration_ms'],
            last_execution_at=stats['last_execution_at'],
            next_execution_at=next_run_at,
            executions_last_hour=executions_last_hour,
            executions_last_24h=executions_last_24h,
            executions_last_7d=executions_last_7d,
            success_rate=stats['success_rate'],
            most_common_error=most_common_error,
            consecutive_failures=stats['consecutive_failures']
        )