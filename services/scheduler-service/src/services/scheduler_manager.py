# services/scheduler-service/src/services/scheduler_manager.py
"""APScheduler integration manager"""

import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from uuid import UUID
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.events import (
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED,
    JobExecutionEvent
)

from shared.utils.logger import ServiceLogger
from ..config import ServiceConfig
from ..models.schedule import Schedule, ScheduleType


class SchedulerManager:
    """Manages APScheduler integration"""
    
    def __init__(
        self,
        config: ServiceConfig,
        job_callback: Callable,
        logger: ServiceLogger
    ):
        self.config = config
        self.job_callback = job_callback
        self.logger = logger
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._started = False
    
    async def start(self):
        """Start the scheduler"""
        if self._started:
            return
        
        # Configure job stores
        jobstores = {
            'default': SQLAlchemyJobStore(
                url=self.config.SCHEDULER_JOB_STORE_URL,
                tablename='apscheduler_jobs'
            )
        }
        
        # Configure executors
        executors = {
            'default': AsyncIOExecutor()
        }
        
        # Configure job defaults
        job_defaults = {
            'coalesce': self.config.SCHEDULER_COALESCE,
            'max_instances': self.config.SCHEDULER_JOB_DEFAULTS_MAX_INSTANCES,
            'misfire_grace_time': self.config.SCHEDULER_MISFIRE_GRACE_TIME
        }
        
        # Create scheduler
        self._scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=pytz.timezone(self.config.SCHEDULER_TIMEZONE)
        )
        
        # Add event listeners
        self._scheduler.add_listener(
            self._handle_job_event,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR | EVENT_JOB_MISSED
        )
        
        # Start scheduler
        self._scheduler.start()
        self._started = True
        
        self.logger.info("Scheduler manager started")
    
    async def stop(self):
        """Stop the scheduler"""
        if self._scheduler and self._started:
            self._scheduler.shutdown(wait=True)
            self._started = False
            self.logger.info("Scheduler manager stopped")
    
    def add_schedule(self, schedule: Schedule) -> str:
        """Add a schedule to APScheduler"""
        if not self._scheduler:
            raise RuntimeError("Scheduler not started")
        
        # Create trigger based on schedule type
        trigger = self._create_trigger(schedule)
        
        # Add job
        job = self._scheduler.add_job(
            func=self.job_callback,
            trigger=trigger,
            id=str(schedule.id),
            name=schedule.name,
            args=[schedule.id],
            kwargs={
                'schedule_name': schedule.name,
                'target_command': schedule.target_command,
                'command_payload': schedule.command_payload
            },
            replace_existing=True,
            max_instances=self.config.SCHEDULER_MAX_INSTANCES
        )
        
        self.logger.info(
            f"Added schedule to APScheduler",
            extra={
                "schedule_id": str(schedule.id),
                "job_id": job.id,
                "next_run": job.next_run_time
            }
        )
        
        return job.id
    
    def remove_schedule(self, schedule_id: UUID) -> bool:
        """Remove a schedule from APScheduler"""
        if not self._scheduler:
            raise RuntimeError("Scheduler not started")
        
        try:
            self._scheduler.remove_job(str(schedule_id))
            self.logger.info(f"Removed schedule from APScheduler: {schedule_id}")
            return True
        except Exception as e:
            self.logger.warning(
                f"Failed to remove schedule from APScheduler: {schedule_id}",
                extra={"error": str(e)}
            )
            return False
    
    def pause_schedule(self, schedule_id: UUID) -> bool:
        """Pause a schedule in APScheduler"""
        if not self._scheduler:
            raise RuntimeError("Scheduler not started")
        
        try:
            self._scheduler.pause_job(str(schedule_id))
            self.logger.info(f"Paused schedule in APScheduler: {schedule_id}")
            return True
        except Exception as e:
            self.logger.warning(
                f"Failed to pause schedule in APScheduler: {schedule_id}",
                extra={"error": str(e)}
            )
            return False
    
    def resume_schedule(self, schedule_id: UUID) -> bool:
        """Resume a schedule in APScheduler"""
        if not self._scheduler:
            raise RuntimeError("Scheduler not started")
        
        try:
            self._scheduler.resume_job(str(schedule_id))
            self.logger.info(f"Resumed schedule in APScheduler: {schedule_id}")
            return True
        except Exception as e:
            self.logger.warning(
                f"Failed to resume schedule in APScheduler: {schedule_id}",
                extra={"error": str(e)}
            )
            return False
    
    def get_next_run_time(self, schedule_id: UUID) -> Optional[datetime]:
        """Get next run time for a schedule"""
        if not self._scheduler:
            return None
        
        job = self._scheduler.get_job(str(schedule_id))
        return job.next_run_time if job else None
    
    def trigger_now(self, schedule_id: UUID) -> bool:
        """Trigger a schedule to run immediately"""
        if not self._scheduler:
            raise RuntimeError("Scheduler not started")
        
        try:
            self._scheduler.modify_job(
                str(schedule_id),
                next_run_time=datetime.now(pytz.timezone(self.config.SCHEDULER_TIMEZONE))
            )
            self.logger.info(f"Triggered schedule to run now: {schedule_id}")
            return True
        except Exception as e:
            self.logger.warning(
                f"Failed to trigger schedule: {schedule_id}",
                extra={"error": str(e)}
            )
            return False
    
    def _create_trigger(self, schedule: Schedule):
        """Create APScheduler trigger from schedule"""
        tz = pytz.timezone(schedule.timezone)
        
        if schedule.schedule_type == ScheduleType.CRON:
            if not schedule.cron_expression:
                raise ValueError("Cron expression required for CRON schedule")
            
            # Parse cron expression
            parts = schedule.cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Invalid cron expression")
            
            return CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
                timezone=tz
            )
        
        elif schedule.schedule_type == ScheduleType.INTERVAL:
            if not schedule.interval_seconds:
                raise ValueError("Interval seconds required for INTERVAL schedule")
            
            return IntervalTrigger(
                seconds=schedule.interval_seconds,
                timezone=tz,
                start_date=datetime.now(tz) + timedelta(seconds=1)
            )
        
        elif schedule.schedule_type == ScheduleType.ONE_TIME:
            if not schedule.scheduled_at:
                raise ValueError("Scheduled time required for ONE_TIME schedule")
            
            return DateTrigger(
                run_date=schedule.scheduled_at,
                timezone=tz
            )
        
        else:
            raise ValueError(f"Unsupported schedule type: {schedule.schedule_type}")
    
    def _handle_job_event(self, event: JobExecutionEvent):
        """Handle APScheduler job events"""
        if event.exception:
            self.logger.error(
                f"Job execution failed",
                extra={
                    "job_id": event.job_id,
                    "error": str(event.exception),
                    "traceback": event.traceback
                }
            )
        elif hasattr(event, 'code') and event.code == EVENT_JOB_MISSED:
            self.logger.warning(
                f"Job execution missed",
                extra={
                    "job_id": event.job_id,
                    "scheduled_run_time": event.scheduled_run_time
                }
            )