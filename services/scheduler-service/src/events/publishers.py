
# services/scheduler-service/src/events/publishers.py
"""Event publishers for scheduler service"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from shared.events import DomainEventPublisher, EventContext, EventContextManager
from shared.events.base import Streams
from shared.events.scheduler.types import (
    SchedulerEvents,
    ScheduleCreatedEventPayload,
    ScheduleUpdatedEventPayload,
    ScheduleDeletedEventPayload,
    SchedulePausedEventPayload,
    ScheduleResumedEventPayload,
    ScheduleTriggeredEventPayload,
    ExecutionStartedEventPayload,
    ExecutionCompletedEventPayload,
    ExecutionFailedEventPayload,
    ScheduleType,
    ExecutionStatus
)


class SchedulerEventPublisher(DomainEventPublisher):
    """Publisher for scheduler service events"""
    domain_stream = Streams.SCHEDULER
    service_name_override = "scheduler-service"
    
    def __init__(self, client, js, logger=None):
        super().__init__(client, js, logger)
        self.context_manager = EventContextManager(logger or self.logger)
    
    async def publish_schedule_created(
        self,
        schedule_id: UUID,
        name: str,
        schedule_type: ScheduleType,
        target_command: str,
        next_run_at: Optional[datetime],
        created_by: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish schedule created event"""
        context = EventContext(
            event_id=str(UUID()),
            event_type=SchedulerEvents.SCHEDULE_CREATED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override,
            metadata={
                **(metadata or {}),
                "schedule_id": str(schedule_id),
                "schedule_name": name
            }
        )
        
        payload = ScheduleCreatedEventPayload(
            schedule_id=schedule_id,
            name=name,
            schedule_type=schedule_type,
            target_command=target_command,
            next_run_at=next_run_at,
            created_by=created_by,
            created_at=datetime.now(timezone.utc)
        )
        
        self.logger.info(
            f"Publishing {context.event_type}",
            extra={
                **context.to_dict(),
                "schedule_name": name,
                "schedule_type": schedule_type
            }
        )
        
        return await self.publish_event_response(
            SchedulerEvents.SCHEDULE_CREATED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=context.metadata
        )
    
    async def publish_schedule_updated(
        self,
        schedule_id: UUID,
        updated_fields: List[str],
        next_run_at: Optional[datetime],
        updated_by: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish schedule updated event"""
        context = EventContext(
            event_id=str(UUID()),
            event_type=SchedulerEvents.SCHEDULE_UPDATED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override,
            metadata={
                **(metadata or {}),
                "schedule_id": str(schedule_id),
                "fields_updated": updated_fields
            }
        )
        
        payload = ScheduleUpdatedEventPayload(
            schedule_id=schedule_id,
            updated_fields=updated_fields,
            next_run_at=next_run_at,
            updated_by=updated_by,
            updated_at=datetime.now(timezone.utc)
        )
        
        return await self.publish_event_response(
            SchedulerEvents.SCHEDULE_UPDATED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=context.metadata
        )
    
    async def publish_schedule_deleted(
        self,
        schedule_id: UUID,
        deleted_by: str,
        hard_delete: bool,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish schedule deleted event"""
        payload = ScheduleDeletedEventPayload(
            schedule_id=schedule_id,
            deleted_by=deleted_by,
            deleted_at=datetime.now(timezone.utc),
            hard_delete=hard_delete
        )
        
        return await self.publish_event_response(
            SchedulerEvents.SCHEDULE_DELETED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=metadata
        )
    
    async def publish_schedule_paused(
        self,
        schedule_id: UUID,
        reason: Optional[str],
        paused_by: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish schedule paused event"""
        payload = SchedulePausedEventPayload(
            schedule_id=schedule_id,
            reason=reason,
            paused_by=paused_by,
            paused_at=datetime.now(timezone.utc)
        )
        
        return await self.publish_event_response(
            SchedulerEvents.SCHEDULE_PAUSED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=metadata
        )
    
    async def publish_schedule_resumed(
        self,
        schedule_id: UUID,
        next_run_at: Optional[datetime],
        resumed_by: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish schedule resumed event"""
        payload = ScheduleResumedEventPayload(
            schedule_id=schedule_id,
            next_run_at=next_run_at,
            resumed_by=resumed_by,
            resumed_at=datetime.now(timezone.utc)
        )
        
        return await self.publish_event_response(
            SchedulerEvents.SCHEDULE_RESUMED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=metadata
        )
    
    async def publish_schedule_triggered(
        self,
        schedule_id: UUID,
        execution_id: UUID,
        triggered_by: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish schedule triggered event"""
        payload = ScheduleTriggeredEventPayload(
            schedule_id=schedule_id,
            execution_id=execution_id,
            triggered_by=triggered_by,
            triggered_at=datetime.now(timezone.utc)
        )
        
        return await self.publish_event_response(
            SchedulerEvents.SCHEDULE_TRIGGERED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=metadata
        )
    
    async def publish_execution_started(
        self,
        execution_id: UUID,
        schedule_id: UUID,
        schedule_name: str,
        target_command: str,
        scheduled_for: datetime,
        attempt_number: int = 1,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish execution started event"""
        context = EventContext(
            event_id=str(UUID()),
            event_type=SchedulerEvents.EXECUTION_STARTED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override,
            metadata={
                **(metadata or {}),
                "execution_id": str(execution_id),
                "schedule_id": str(schedule_id),
                "target_command": target_command
            }
        )
        
        payload = ExecutionStartedEventPayload(
            execution_id=execution_id,
            schedule_id=schedule_id,
            schedule_name=schedule_name,
            target_command=target_command,
            scheduled_for=scheduled_for,
            started_at=datetime.now(timezone.utc),
            attempt_number=attempt_number
        )
        
        self.logger.info(
            f"Publishing {context.event_type}",
            extra={
                **context.to_dict(),
                "schedule_name": schedule_name,
                "attempt": attempt_number
            }
        )
        
        return await self.publish_event_response(
            SchedulerEvents.EXECUTION_STARTED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=context.metadata
        )
    
    async def publish_execution_completed(
        self,
        execution_id: UUID,
        schedule_id: UUID,
        status: ExecutionStatus,
        duration_ms: int,
        next_run_at: Optional[datetime],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish execution completed event"""
        context = EventContext(
            event_id=str(UUID()),
            event_type=SchedulerEvents.EXECUTION_COMPLETED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override,
            metadata={
                **(metadata or {}),
                "execution_id": str(execution_id),
                "schedule_id": str(schedule_id),
                "status": status,
                "duration_ms": duration_ms
            }
        )
        
        payload = ExecutionCompletedEventPayload(
            execution_id=execution_id,
            schedule_id=schedule_id,
            status=status,
            duration_ms=duration_ms,
            completed_at=datetime.now(timezone.utc),
            next_run_at=next_run_at
        )
        
        self.logger.info(
            f"Publishing {context.event_type}",
            extra={
                **context.to_dict(),
                "status": status,
                "duration_ms": duration_ms
            }
        )
        
        return await self.publish_event_response(
            SchedulerEvents.EXECUTION_COMPLETED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=context.metadata
        )
    
    async def publish_execution_failed(
        self,
        execution_id: UUID,
        schedule_id: UUID,
        error_message: str,
        error_type: Optional[str],
        will_retry: bool,
        retry_at: Optional[datetime],
        attempt_number: int,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish execution failed event"""
        context = EventContext(
            event_id=str(UUID()),
            event_type=SchedulerEvents.EXECUTION_FAILED,
            correlation_id=correlation_id,
            timestamp=datetime.now(timezone.utc),
            source_service=self.service_name_override,
            metadata={
                **(metadata or {}),
                "execution_id": str(execution_id),
                "schedule_id": str(schedule_id),
                "will_retry": will_retry,
                "attempt": attempt_number
            }
        )
        
        payload = ExecutionFailedEventPayload(
            execution_id=execution_id,
            schedule_id=schedule_id,
            error_message=error_message,
            error_type=error_type,
            will_retry=will_retry,
            retry_at=retry_at,
            attempt_number=attempt_number,
            failed_at=datetime.now(timezone.utc)
        )
        
        self.logger.error(
            f"Publishing {context.event_type}",
            extra={
                **context.to_dict(),
                "error": error_message,
                "will_retry": will_retry
            }
        )
        
        return await self.publish_event_response(
            SchedulerEvents.EXECUTION_FAILED,
            payload.model_dump(),
            correlation_id=correlation_id,
            metadata=context.metadata
        )


def get_publishers():
    """Get all publishers for this service"""
    return [SchedulerEventPublisher]