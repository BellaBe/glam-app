# services/scheduler-service/src/services/job_executor.py
"""Job execution service"""

import asyncio
import time
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime

from shared.utils.logger import ServiceLogger
from shared.messaging.publisher import JetStreamEventPublisher
from ..config import ServiceConfig
from ..models.execution import ScheduleExecution, ExecutionStatus
from ..repositories.schedule_repository import ScheduleRepository
from ..repositories.execution_repository import ExecutionRepository
from ..events.publishers import SchedulerEventPublisher
from ..utils.distributed_lock import DistributedLock


class JobExecutor:
    """Handles job execution logic"""
    
    def __init__(
        self,
        config: ServiceConfig,
        schedule_repo: ScheduleRepository,
        execution_repo: ExecutionRepository,
        base_publisher: JetStreamEventPublisher,
        event_publisher: SchedulerEventPublisher,
        distributed_lock: DistributedLock,
        logger: ServiceLogger
    ):
        self.config = config
        self.schedule_repo = schedule_repo
        self.execution_repo = execution_repo
        self.base_publisher = base_publisher
        self.event_publisher = event_publisher
        self.distributed_lock = distributed_lock
        self.logger = logger
    
    async def execute_job(
        self,
        schedule_id: UUID,
        **kwargs
    ) -> None:
        """Execute a scheduled job"""
        
        # Get schedule details
        schedule = await self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            self.logger.error(f"Schedule not found: {schedule_id}")
            return
        
        # Check if schedule is active
        if not schedule.is_active or schedule.is_paused:
            self.logger.info(
                f"Skipping inactive/paused schedule: {schedule_id}",
                extra={
                    "is_active": schedule.is_active,
                    "is_paused": schedule.is_paused
                }
            )
            return
        
        # Create execution record
        execution = ScheduleExecution(
            schedule_id=schedule_id,
            scheduled_for=datetime.utcnow(),
            status=ExecutionStatus.PENDING,
            correlation_id=str(uuid4()),
            command_sent=schedule.target_command,
            command_payload=schedule.command_payload
        )
        execution = await self.execution_repo.create(execution)
        
        # Acquire distributed lock
        lock_key = f"schedule:{schedule_id}:execution"
        lock_acquired = False
        
        try:
            lock_acquired = await self.distributed_lock.acquire(
                lock_key,
                ttl=self.config.LOCK_TIMEOUT_SECONDS
            )
            
            if not lock_acquired:
                self.logger.warning(
                    f"Could not acquire lock for schedule: {schedule_id}",
                    extra={"lock_key": lock_key}
                )
                
                # Mark as skipped
                await self.execution_repo.update_status(
                    execution.id,
                    ExecutionStatus.SKIPPED,
                    error_message="Could not acquire execution lock"
                )
                return
            
            # Update lock ID
            execution.lock_id = self.distributed_lock.get_lock_id(lock_key)
            
            # Start execution
            start_time = time.time()
            await self.execution_repo.update_status(
                execution.id,
                ExecutionStatus.RUNNING,
                started_at=datetime.utcnow()
            )
            
            # Publish execution started event
            await self.event_publisher.publish_execution_started(
                execution_id=execution.id,
                schedule_id=schedule_id,
                schedule_name=schedule.name,
                target_command=schedule.target_command,
                scheduled_for=execution.scheduled_for,
                attempt_number=execution.attempt_number,
                correlation_id=execution.correlation_id
            )
            
            # Execute the command
            try:
                await self._send_command(
                    target_command=schedule.target_command,
                    command_payload=schedule.command_payload,
                    correlation_id=execution.correlation_id,
                    metadata={
                        "schedule_id": str(schedule_id),
                        "execution_id": str(execution.id),
                        "schedule_name": schedule.name
                    }
                )
                
                # Calculate duration
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Mark as successful
                await self.execution_repo.update_status(
                    execution.id,
                    ExecutionStatus.SUCCESS,
                    completed_at=datetime.utcnow(),
                    duration_ms=duration_ms
                )
                
                # Update schedule stats
                await self.schedule_repo.update_last_run(
                    schedule_id,
                    last_run_at=datetime.utcnow(),
                    increment_success=True
                )
                
                # Get next run time (from APScheduler)
                next_run_at = kwargs.get('next_run_at')
                
                # Publish completion event
                await self.event_publisher.publish_execution_completed(
                    execution_id=execution.id,
                    schedule_id=schedule_id,
                    status=ExecutionStatus.SUCCESS,
                    duration_ms=duration_ms,
                    next_run_at=next_run_at,
                    correlation_id=execution.correlation_id
                )
                
                self.logger.info(
                    f"Successfully executed schedule: {schedule_id}",
                    extra={
                        "execution_id": str(execution.id),
                        "duration_ms": duration_ms,
                        "correlation_id": execution.correlation_id
                    }
                )
                
            except Exception as e:
                # Handle execution failure
                await self._handle_execution_failure(
                    schedule=schedule,
                    execution=execution,
                    error=e,
                    start_time=start_time
                )
                
        finally:
            # Release lock
            if lock_acquired:
                await self.distributed_lock.release(lock_key)
    
    async def execute_command(
        self,
        target_command: str,
        command_payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        priority: int = 5
    ) -> None:
        """Execute a command immediately without scheduling"""
        
        if not correlation_id:
            correlation_id = str(uuid4())
        
        self.logger.info(
            f"Executing immediate command: {target_command}",
            extra={
                "target_command": target_command,
                "correlation_id": correlation_id,
                "priority": priority
            }
        )
        
        await self._send_command(
            target_command=target_command,
            command_payload=command_payload,
            correlation_id=correlation_id,
            metadata={
                "execution_type": "immediate",
                "priority": priority
            }
        )
    
    async def _send_command(
        self,
        target_command: str,
        command_payload: Dict[str, Any],
        correlation_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Send command to target service"""
        
        # Validate command is allowed
        if target_command not in self.config.ALLOWED_TARGET_COMMANDS:
            raise ValueError(f"Command not allowed: {target_command}")
        
        # Send command
        await self.base_publisher.publish_command(
            command_type=target_command,
            payload=command_payload,
            correlation_id=correlation_id,
            metadata=metadata
        )
        
        self.logger.info(
            f"Sent command: {target_command}",
            extra={
                "target_command": target_command,
                "correlation_id": correlation_id,
                "metadata": metadata
            }
        )
    
    async def _handle_execution_failure(
        self,
        schedule,
        execution: ScheduleExecution,
        error: Exception,
        start_time: float
    ) -> None:
        """Handle execution failure"""
        
        duration_ms = int((time.time() - start_time) * 1000)
        error_message = str(error)
        error_type = type(error).__name__
        
        # Update execution status
        await self.execution_repo.update_status(
            execution.id,
            ExecutionStatus.FAILED,
            completed_at=datetime.utcnow(),
            duration_ms=duration_ms,
            error_message=error_message,
            error_type=error_type
        )
        
        # Update schedule failure count
        await self.schedule_repo.update_last_run(
            schedule.id,
            last_run_at=datetime.utcnow(),
            increment_success=False
        )
        
        # Check if we should retry
        will_retry = execution.attempt_number < schedule.max_retries
        retry_at = None
        
        if will_retry:
            retry_at = datetime.utcnow() + timedelta(
                seconds=schedule.retry_delay_seconds
            )
            
            # Create retry execution
            retry_execution = ScheduleExecution(
                schedule_id=schedule.id,
                scheduled_for=retry_at,
                status=ExecutionStatus.PENDING,
                correlation_id=execution.correlation_id,
                command_sent=schedule.target_command,
                command_payload=schedule.command_payload,
                attempt_number=execution.attempt_number + 1
            )
            await self.execution_repo.create(retry_execution)
            
            # TODO: Schedule retry with APScheduler
        
        # Publish failure event
        await self.event_publisher.publish_execution_failed(
            execution_id=execution.id,
            schedule_id=schedule.id,
            error_message=error_message,
            error_type=error_type,
            will_retry=will_retry,
            retry_at=retry_at,
            attempt_number=execution.attempt_number,
            correlation_id=execution.correlation_id
        )
        
        self.logger.error(
            f"Failed to execute schedule: {schedule.id}",
            extra={
                "execution_id": str(execution.id),
                "error": error_message,
                "error_type": error_type,
                "will_retry": will_retry,
                "attempt": execution.attempt_number
            }
        )