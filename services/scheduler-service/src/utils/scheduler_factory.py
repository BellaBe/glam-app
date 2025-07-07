# services/scheduler-service/src/utils/scheduler_factory.py
"""Factory for creating scheduler callback function"""

import asyncio
from typing import Callable
from uuid import UUID

from ..services.job_executor import JobExecutor


def create_scheduler_callback(job_executor: JobExecutor) -> Callable:
    """
    Create a callback function for APScheduler
    
    APScheduler expects a synchronous function, so we create a wrapper
    that runs the async job executor in the event loop.
    """
    
    def scheduler_callback(schedule_id: UUID, **kwargs):
        """Callback function that APScheduler will call"""
        # Get the event loop
        loop = asyncio.get_event_loop()
        
        # Schedule the async job execution
        loop.create_task(
            job_executor.execute_job(schedule_id, **kwargs)
        )
    
    return scheduler_callback