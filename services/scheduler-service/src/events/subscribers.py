# services/scheduler-service/src/events/subscribers.py
"""Event subscribers for scheduler service"""

import time
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import ValidationError

from shared.events import DomainEventSubscriber, EventContextManager, EventContext
from shared.events.scheduler.types import (
    SchedulerCommands,
    CreateScheduleCommandPayload,
    UpdateScheduleCommandPayload,
    DeleteScheduleCommandPayload,
    PauseScheduleCommandPayload,
    ResumeScheduleCommandPayload,
    TriggerScheduleCommandPayload,
    ExecuteImmediateCommandPayload
)
from shared.messaging.publisher import JetStreamEventPublisher

from ..services.schedule_service import ScheduleService
from ..services.job_executor import JobExecutor


class SchedulerEventSubscriber(DomainEventSubscriber):
    """Base class for scheduler event subscribers"""
    
    def __init__(self):
        super().__init__()
        self.context_manager = EventContextManager(self.logger)
        self.schedule_service: Optional[ScheduleService] = None
        self.job_executor: Optional[JobExecutor] = None
        self.base_publisher: Optional[JetStreamEventPublisher] = None
    
    def set_schedule_service(self, service: ScheduleService):
        """Inject schedule service"""
        self.schedule_service = service
    
    def set_job_executor(self, executor: JobExecutor):
        """Inject job executor"""
        self.job_executor = executor
    
    def set_base_publisher(self, publisher: JetStreamEventPublisher):
        """Inject base publisher for sending commands to other services"""
        self.base_publisher = publisher


class CreateScheduleSubscriber(SchedulerEventSubscriber):
    """Subscriber for schedule creation commands"""
    
    event_type = SchedulerCommands.SCHEDULE_CREATE
    queue_group = "scheduler-service-create"
    
    async def handle(self, data: Dict[str, Any], context: EventContext) -> None:
        """Handle schedule creation command"""
        start_time = time.time()
        
        try:
            # Parse and validate payload
            payload = CreateScheduleCommandPayload(**data)
            
            self.logger.info(
                f"Creating schedule: {payload.name}",
                extra={
                    **context.to_dict(),
                    "schedule_name": payload.name,
                    "schedule_type": payload.schedule_type
                }
            )
            
            # Create schedule
            schedule = await self.schedule_service.create_schedule(
                create_data=payload,
                created_by=context.source_service,
                correlation_id=context.correlation_id
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.info(
                f"Schedule created: {schedule.id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(schedule.id),
                    "duration_ms": duration_ms
                }
            )
            
        except ValidationError as e:
            self.logger.error(
                f"Invalid payload for {self.event_type}",
                extra={
                    **context.to_dict(),
                    "validation_errors": e.errors()
                }
            )
            raise
        except Exception as e:
            self.logger.error(
                f"Failed to create schedule",
                extra={
                    **context.to_dict(),
                    "error": str(e)
                }
            )
            raise


class UpdateScheduleSubscriber(SchedulerEventSubscriber):
    """Subscriber for schedule update commands"""
    
    event_type = SchedulerCommands.SCHEDULE_UPDATE
    queue_group = "scheduler-service-update"
    
    async def handle(self, data: Dict[str, Any], context: EventContext) -> None:
        """Handle schedule update command"""
        try:
            payload = UpdateScheduleCommandPayload(**data)
            
            self.logger.info(
                f"Updating schedule: {payload.schedule_id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(payload.schedule_id)
                }
            )
            
            # Update schedule
            schedule = await self.schedule_service.update_schedule(
                schedule_id=payload.schedule_id,
                update_data=payload,
                updated_by=context.source_service,
                correlation_id=context.correlation_id
            )
            
            self.logger.info(
                f"Schedule updated: {schedule.id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(schedule.id)
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to update schedule",
                extra={
                    **context.to_dict(),
                    "error": str(e)
                }
            )
            raise


class DeleteScheduleSubscriber(SchedulerEventSubscriber):
    """Subscriber for schedule deletion commands"""
    
    event_type = SchedulerCommands.SCHEDULE_DELETE
    queue_group = "scheduler-service-delete"
    
    async def handle(self, data: Dict[str, Any], context: EventContext) -> None:
        """Handle schedule deletion command"""
        try:
            payload = DeleteScheduleCommandPayload(**data)
            
            self.logger.info(
                f"Deleting schedule: {payload.schedule_id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(payload.schedule_id),
                    "hard_delete": payload.hard_delete
                }
            )
            
            # Delete schedule
            await self.schedule_service.delete_schedule(
                schedule_id=payload.schedule_id,
                deleted_by=context.source_service,
                hard_delete=payload.hard_delete,
                correlation_id=context.correlation_id
            )
            
            self.logger.info(
                f"Schedule deleted: {payload.schedule_id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(payload.schedule_id)
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to delete schedule",
                extra={
                    **context.to_dict(),
                    "error": str(e)
                }
            )
            raise


class PauseScheduleSubscriber(SchedulerEventSubscriber):
    """Subscriber for schedule pause commands"""
    
    event_type = SchedulerCommands.SCHEDULE_PAUSE
    queue_group = "scheduler-service-pause"
    
    async def handle(self, data: Dict[str, Any], context: EventContext) -> None:
        """Handle schedule pause command"""
        try:
            payload = PauseScheduleCommandPayload(**data)
            
            self.logger.info(
                f"Pausing schedule: {payload.schedule_id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(payload.schedule_id),
                    "reason": payload.reason
                }
            )
            
            # Pause schedule
            await self.schedule_service.pause_schedule(
                schedule_id=payload.schedule_id,
                paused_by=context.source_service,
                reason=payload.reason,
                correlation_id=context.correlation_id
            )
            
            self.logger.info(
                f"Schedule paused: {payload.schedule_id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(payload.schedule_id)
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to pause schedule",
                extra={
                    **context.to_dict(),
                    "error": str(e)
                }
            )
            raise


class ResumeScheduleSubscriber(SchedulerEventSubscriber):
    """Subscriber for schedule resume commands"""
    
    event_type = SchedulerCommands.SCHEDULE_RESUME
    queue_group = "scheduler-service-resume"
    
    async def handle(self, data: Dict[str, Any], context: EventContext) -> None:
        """Handle schedule resume command"""
        try:
            payload = ResumeScheduleCommandPayload(**data)
            
            self.logger.info(
                f"Resuming schedule: {payload.schedule_id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(payload.schedule_id)
                }
            )
            
            # Resume schedule
            await self.schedule_service.resume_schedule(
                schedule_id=payload.schedule_id,
                resumed_by=context.source_service,
                correlation_id=context.correlation_id
            )
            
            self.logger.info(
                f"Schedule resumed: {payload.schedule_id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(payload.schedule_id)
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to resume schedule",
                extra={
                    **context.to_dict(),
                    "error": str(e)
                }
            )
            raise


class TriggerScheduleSubscriber(SchedulerEventSubscriber):
    """Subscriber for schedule trigger commands"""
    
    event_type = SchedulerCommands.SCHEDULE_TRIGGER
    queue_group = "scheduler-service-trigger"
    
    async def handle(self, data: Dict[str, Any], context: EventContext) -> None:
        """Handle schedule trigger command"""
        try:
            payload = TriggerScheduleCommandPayload(**data)
            
            self.logger.info(
                f"Triggering schedule: {payload.schedule_id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(payload.schedule_id)
                }
            )
            
            # Trigger schedule execution
            execution_id = await self.schedule_service.trigger_schedule(
                schedule_id=payload.schedule_id,
                triggered_by=context.source_service,
                override_payload=payload.override_payload,
                correlation_id=context.correlation_id
            )
            
            self.logger.info(
                f"Schedule triggered: {payload.schedule_id}",
                extra={
                    **context.to_dict(),
                    "schedule_id": str(payload.schedule_id),
                    "execution_id": str(execution_id)
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to trigger schedule",
                extra={
                    **context.to_dict(),
                    "error": str(e)
                }
            )
            raise


class ExecuteImmediateSubscriber(SchedulerEventSubscriber):
    """Subscriber for immediate execution commands"""
    
    event_type = SchedulerCommands.EXECUTE_IMMEDIATE
    queue_group = "scheduler-service-immediate"
    
    async def handle(self, data: Dict[str, Any], context: EventContext) -> None:
        """Handle immediate execution command"""
        start_time = time.time()
        
        try:
            payload = ExecuteImmediateCommandPayload(**data)
            
            self.logger.info(
                f"Executing immediate command: {payload.target_command}",
                extra={
                    **context.to_dict(),
                    "target_command": payload.target_command
                }
            )
            
            # Execute command immediately
            await self.job_executor.execute_command(
                target_command=payload.target_command,
                command_payload=payload.command_payload,
                correlation_id=context.correlation_id,
                priority=payload.priority
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            self.logger.info(
                f"Immediate command executed: {payload.target_command}",
                extra={
                    **context.to_dict(),
                    "target_command": payload.target_command,
                    "duration_ms": duration_ms
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to execute immediate command",
                extra={
                    **context.to_dict(),
                    "error": str(e)
                }
            )
            raise


def get_subscribers():
    """Get all subscribers for this service"""
    return [
        CreateScheduleSubscriber,
        UpdateScheduleSubscriber,
        DeleteScheduleSubscriber,
        PauseScheduleSubscriber,
        ResumeScheduleSubscriber,
        TriggerScheduleSubscriber,
        ExecuteImmediateSubscriber
    ]