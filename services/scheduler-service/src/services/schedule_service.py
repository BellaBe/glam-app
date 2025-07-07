# services/scheduler-service/src/services/schedule_service.py
"""Schedule management service"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime

from shared.utils.logger import ServiceLogger
from shared.events.scheduler.types import (
    CreateScheduleCommandPayload,
    UpdateScheduleCommandPayload,
    ScheduleType
)
from ..config import ServiceConfig
from ..models.schedule import Schedule, ScheduleStatus
from ..repositories.schedule_repository import ScheduleRepository
from ..mappers.schedule_mapper import ScheduleMapper
from ..events.publishers import SchedulerEventPublisher
from ..exceptions import (
    ScheduleNotFoundError,
    ScheduleAlreadyExistsError,
    ScheduleLimitExceededError,
    InvalidScheduleError
)
from .scheduler_manager import SchedulerManager


class ScheduleService:
    """Service for managing schedules"""
    
    def __init__(
        self,
        config: ServiceConfig,
        schedule_repo: ScheduleRepository,
        schedule_mapper: ScheduleMapper,
        event_publisher: SchedulerEventPublisher,
        scheduler_manager: SchedulerManager,
        logger: ServiceLogger
    ):
        self.config = config
        self.schedule_repo = schedule_repo
        self.schedule_mapper = schedule_mapper
        self.event_publisher = event_publisher
        self.scheduler_manager = scheduler_manager
        self.logger = logger
    
    async def create_schedule(
        self,
        create_data: CreateScheduleCommandPayload,
        created_by: str,
        correlation_id: Optional[str] = None
    ) -> Schedule:
        """Create a new schedule"""
        
        self.logger.info(
            f"Creating schedule: {create_data.name}",
            extra={
                "schedule_name": create_data.name,
                "schedule_type": create_data.schedule_type,
                "created_by": created_by,
                "correlation_id": correlation_id
            }
        )
        
        # Validate command is allowed
        if create_data.target_command not in self.config.ALLOWED_TARGET_COMMANDS:
            raise InvalidScheduleError(
                f"Target command not allowed: {create_data.target_command}"
            )
        
        # Check if schedule with same name exists for creator
        existing = await self.schedule_repo.get_by_name_and_creator(
            create_data.name,
            created_by
        )
        if existing:
            raise ScheduleAlreadyExistsError(
                f"Schedule with name '{create_data.name}' already exists",
                schedule_name=create_data.name
            )
        
        # Check schedule limit for creator
        count = await self.schedule_repo.count_by_creator(created_by)
        if count >= self.config.MAX_SCHEDULES_PER_CREATOR:
            raise ScheduleLimitExceededError(
                f"Schedule limit exceeded for {created_by}",
                limit=self.config.MAX_SCHEDULES_PER_CREATOR
            )
        
        # Map to model
        schedule = self.schedule_mapper.create_to_model(
            create_data,
            created_by=created_by or create_data.created_by,
            correlation_id=correlation_id
        )
        
        # Calculate next run time based on schedule type
        if schedule.schedule_type == ScheduleType.IMMEDIATE:
            # Immediate schedules run once and complete
            schedule.next_run_at = datetime.utcnow()
            schedule.status = ScheduleStatus.COMPLETED
        else:
            # Add to APScheduler to get next run time
            job_id = self.scheduler_manager.add_schedule(schedule)
            schedule.job_id = job_id
            schedule.next_run_at = self.scheduler_manager.get_next_run_time(schedule.id)
        
        # Save to database
        schedule = await self.schedule_repo.create(schedule)
        
        # Publish event
        await self.event_publisher.publish_schedule_created(
            schedule_id=schedule.id,
            name=schedule.name,
            schedule_type=schedule.schedule_type,
            target_command=schedule.target_command,
            next_run_at=schedule.next_run_at,
            created_by=created_by,
            correlation_id=correlation_id
        )
        
        self.logger.info(
            f"Schedule created: {schedule.id}",
            extra={
                "schedule_id": str(schedule.id),
                "schedule_name": schedule.name,
                "next_run_at": schedule.next_run_at
            }
        )
        
        return schedule
    
    async def update_schedule(
        self,
        schedule_id: UUID,
        update_data: UpdateScheduleCommandPayload,
        updated_by: str,
        correlation_id: Optional[str] = None
    ) -> Schedule:
        """Update a schedule"""
        
        self.logger.info(
            f"Updating schedule: {schedule_id}",
            extra={
                "schedule_id": str(schedule_id),
                "updated_by": updated_by,
                "correlation_id": correlation_id
            }
        )
        
        # Get existing schedule
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(
                f"Schedule not found: {schedule_id}",
                schedule_id=schedule_id
            )
        
        # Validate command if updating
        if update_data.target_command and update_data.target_command not in self.config.ALLOWED_TARGET_COMMANDS:
            raise InvalidScheduleError(
                f"Target command not allowed: {update_data.target_command}"
            )
        
        # Apply updates
        schedule = self.schedule_mapper.update_to_model(
            schedule,
            update_data,
            updated_by=updated_by
        )
        
        # If schedule configuration changed, update APScheduler
        schedule_fields = ['schedule_type', 'cron_expression', 'interval_seconds', 'scheduled_at', 'timezone']
        if any(field in schedule._updated_fields for field in schedule_fields):
            # Remove old job
            self.scheduler_manager.remove_schedule(schedule_id)
            
            # Add updated job
            if schedule.is_active and not schedule.is_paused:
                job_id = self.scheduler_manager.add_schedule(schedule)
                schedule.job_id = job_id
                schedule.next_run_at = self.scheduler_manager.get_next_run_time(schedule_id)
        
        # Save to database
        schedule = await self.schedule_repo.update(schedule)
        
        # Publish event
        await self.event_publisher.publish_schedule_updated(
            schedule_id=schedule.id,
            updated_fields=schedule._updated_fields,
            next_run_at=schedule.next_run_at,
            updated_by=updated_by,
            correlation_id=correlation_id
        )
        
        self.logger.info(
            f"Schedule updated: {schedule.id}",
            extra={
                "schedule_id": str(schedule.id),
                "updated_fields": schedule._updated_fields
            }
        )
        
        return schedule
    
    async def delete_schedule(
        self,
        schedule_id: UUID,
        deleted_by: str,
        hard_delete: bool = False,
        correlation_id: Optional[str] = None
    ) -> None:
        """Delete a schedule"""
        
        self.logger.info(
            f"Deleting schedule: {schedule_id}",
            extra={
                "schedule_id": str(schedule_id),
                "deleted_by": deleted_by,
                "hard_delete": hard_delete,
                "correlation_id": correlation_id
            }
        )
        
        # Get schedule
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(
                f"Schedule not found: {schedule_id}",
                schedule_id=schedule_id
            )
        
        # Remove from APScheduler
        self.scheduler_manager.remove_schedule(schedule_id)
        
        # Delete from database
        if hard_delete:
            await self.schedule_repo.delete(schedule_id)
        else:
            await self.schedule_repo.soft_delete(schedule_id, deleted_by)
        
        # Publish event
        await self.event_publisher.publish_schedule_deleted(
            schedule_id=schedule_id,
            deleted_by=deleted_by,
            hard_delete=hard_delete,
            correlation_id=correlation_id
        )
        
        self.logger.info(
            f"Schedule deleted: {schedule_id}",
            extra={
                "schedule_id": str(schedule_id),
                "hard_delete": hard_delete
            }
        )
    
    async def pause_schedule(
        self,
        schedule_id: UUID,
        paused_by: str,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Schedule:
        """Pause a schedule"""
        
        self.logger.info(
            f"Pausing schedule: {schedule_id}",
            extra={
                "schedule_id": str(schedule_id),
                "paused_by": paused_by,
                "reason": reason,
                "correlation_id": correlation_id
            }
        )
        
        # Get schedule
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(
                f"Schedule not found: {schedule_id}",
                schedule_id=schedule_id
            )
        
        # Update state
        schedule.is_paused = True
        schedule.pause_reason = reason
        schedule.updated_by = paused_by
        schedule.updated_at = datetime.utcnow()
        
        # Pause in APScheduler
        self.scheduler_manager.pause_schedule(schedule_id)
        
        # Save to database
        schedule = await self.schedule_repo.update(schedule)
        
        # Publish event
        await self.event_publisher.publish_schedule_paused(
            schedule_id=schedule_id,
            reason=reason,
            paused_by=paused_by,
            correlation_id=correlation_id
        )
        
        self.logger.info(
            f"Schedule paused: {schedule_id}",
            extra={"schedule_id": str(schedule_id)}
        )
        
        return schedule
    
    async def resume_schedule(
        self,
        schedule_id: UUID,
        resumed_by: str,
        correlation_id: Optional[str] = None
    ) -> Schedule:
        """Resume a paused schedule"""
        
        self.logger.info(
            f"Resuming schedule: {schedule_id}",
            extra={
                "schedule_id": str(schedule_id),
                "resumed_by": resumed_by,
                "correlation_id": correlation_id
            }
        )
        
        # Get schedule
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(
                f"Schedule not found: {schedule_id}",
                schedule_id=schedule_id
            )
        
        # Update state
        schedule.is_paused = False
        schedule.pause_reason = None
        schedule.updated_by = resumed_by
        schedule.updated_at = datetime.utcnow()
        
        # Resume in APScheduler
        self.scheduler_manager.resume_schedule(schedule_id)
        schedule.next_run_at = self.scheduler_manager.get_next_run_time(schedule_id)
        
        # Save to database
        schedule = await self.schedule_repo.update(schedule)
        
        # Publish event
        await self.event_publisher.publish_schedule_resumed(
            schedule_id=schedule_id,
            next_run_at=schedule.next_run_at,
            resumed_by=resumed_by,
            correlation_id=correlation_id
        )
        
        self.logger.info(
            f"Schedule resumed: {schedule_id}",
            extra={
                "schedule_id": str(schedule_id),
                "next_run_at": schedule.next_run_at
            }
        )
        
        return schedule
    
    async def trigger_schedule(
        self,
        schedule_id: UUID,
        triggered_by: str,
        override_payload: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ) -> UUID:
        """Trigger a schedule to run immediately"""
        
        self.logger.info(
            f"Triggering schedule: {schedule_id}",
            extra={
                "schedule_id": str(schedule_id),
                "triggered_by": triggered_by,
                "correlation_id": correlation_id
            }
        )
        
        # Get schedule
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(
                f"Schedule not found: {schedule_id}",
                schedule_id=schedule_id
            )
        
        # Create execution ID
        execution_id = uuid4()
        
        # Trigger in APScheduler
        self.scheduler_manager.trigger_now(schedule_id)
        
        # Publish event
        await self.event_publisher.publish_schedule_triggered(
            schedule_id=schedule_id,
            execution_id=execution_id,
            triggered_by=triggered_by,
            correlation_id=correlation_id
        )
        
        self.logger.info(
            f"Schedule triggered: {schedule_id}",
            extra={
                "schedule_id": str(schedule_id),
                "execution_id": str(execution_id)
            }
        )
        
        return execution_id
    
    async def list_schedules(
        self,
        offset: int = 0,
        limit: int = 100,
        creator: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: Optional[ScheduleStatus] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Schedule], int]:
        """List schedules with filters"""
        
        filters = []
        
        if creator:
            filters.append(Schedule.created_by == creator)
        
        if status:
            filters.append(Schedule.status == status)
        
        if is_active is not None:
            filters.append(Schedule.is_active == is_active)
        
        # Add default filter for non-deleted
        filters.append(Schedule.deleted_at.is_(None))
        
        # Get schedules
        if tags:
            schedules = await self.schedule_repo.get_by_tags(tags, offset, limit)
            # Count would need to be implemented for tag filtering
            total = len(schedules)  # Simplified
        else:
            schedules = await self.schedule_repo.get_all(offset, limit, filters)
            total = await self.schedule_repo.count(filters)
        
        return schedules, total
    
    async def get_schedule(self, schedule_id: UUID) -> Schedule:
        """Get a schedule by ID"""
        
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise ScheduleNotFoundError(
                f"Schedule not found: {schedule_id}",
                schedule_id=schedule_id
            )
        
        return schedule
    
    async def bulk_create(
        self,
        schedules: List[CreateScheduleCommandPayload],
        created_by: str,
        correlation_id: Optional[str] = None
    ) -> List[Schedule]:
        """Bulk create schedules"""
        
        if len(schedules) > self.config.MAX_BULK_OPERATIONS:
            raise InvalidScheduleError(
                f"Bulk operation limit exceeded: {len(schedules)} > {self.config.MAX_BULK_OPERATIONS}"
            )
        
        created_schedules = []
        
        for schedule_data in schedules:
            try:
                schedule = await self.create_schedule(
                    schedule_data,
                    created_by,
                    correlation_id
                )
                created_schedules.append(schedule)
            except Exception as e:
                self.logger.error(
                    f"Failed to create schedule in bulk operation: {schedule_data.name}",
                    extra={
                        "error": str(e),
                        "schedule_name": schedule_data.name
                    }
                )
                # Continue with other schedules
        
        return created_schedules
    
    async def bulk_operation(
        self,
        schedule_ids: List[UUID],
        operation: str,
        performed_by: str,
        reason: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform bulk operation on schedules"""
        
        if len(schedule_ids) > self.config.MAX_BULK_OPERATIONS:
            raise InvalidScheduleError(
                f"Bulk operation limit exceeded: {len(schedule_ids)} > {self.config.MAX_BULK_OPERATIONS}"
            )
        
        results = {
            "success": [],
            "failed": []
        }
        
        for schedule_id in schedule_ids:
            try:
                if operation == "pause":
                    await self.pause_schedule(schedule_id, performed_by, reason, correlation_id)
                elif operation == "resume":
                    await self.resume_schedule(schedule_id, performed_by, correlation_id)
                elif operation == "delete":
                    await self.delete_schedule(schedule_id, performed_by, False, correlation_id)
                else:
                    raise ValueError(f"Invalid operation: {operation}")
                
                results["success"].append(str(schedule_id))
                
            except Exception as e:
                self.logger.error(
                    f"Failed bulk operation on schedule: {schedule_id}",
                    extra={
                        "error": str(e),
                        "schedule_id": str(schedule_id),
                        "operation": operation
                    }
                )
                results["failed"].append({
                    "schedule_id": str(schedule_id),
                    "error": str(e)
                })
        
        return results