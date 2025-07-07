# services/scheduler-service/src/dependencies.py
"""
FastAPI dependency injection for scheduler service.

This module provides dependency functions for accessing service
components within API routes.
"""

from typing import Annotated, Any
from fastapi import Depends, HTTPException, Request

from shared.messaging import JetStreamWrapper
from .lifecycle import ServiceLifecycle
from .events.publishers import SchedulerEventPublisher
from .services.schedule_service import ScheduleService
from .services.job_executor import JobExecutor
from .services.scheduler_manager import SchedulerManager
from .repositories.schedule_repository import ScheduleRepository
from .repositories.execution_repository import ExecutionRepository


# ------------------------------- core -------------------------------------- #
def get_lifecycle(request: Request) -> ServiceLifecycle:
    return request.app.state.lifecycle


def get_config(request: Request):
    return request.app.state.config


# Type aliases for core dependencies
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[Any, Depends(get_config)]  # Replace Any with your Config type


# ------------------------------- messaging --------------------------------- #
def get_messaging_wrapper(lifecycle: LifecycleDep) -> JetStreamWrapper:
    if not lifecycle.messaging_wrapper:
        raise HTTPException(500, "Messaging not initialized")
    return lifecycle.messaging_wrapper


def get_publisher(wrapper: "MessagingDep") -> SchedulerEventPublisher:
    pub = wrapper.get_publisher(SchedulerEventPublisher)
    if not pub:
        raise HTTPException(500, "SchedulerEventPublisher not initialized")
    return pub


# Type aliases for messaging
MessagingDep = Annotated[JetStreamWrapper, Depends(get_messaging_wrapper)]
PublisherDep = Annotated[SchedulerEventPublisher, Depends(get_publisher)]


# ----------------------------- repositories -------------------------------- #
def get_schedule_repository(lifecycle: LifecycleDep) -> ScheduleRepository:
    if not lifecycle.schedule_repo:
        raise HTTPException(500, "ScheduleRepository not initialized")
    return lifecycle.schedule_repo


def get_execution_repository(lifecycle: LifecycleDep) -> ExecutionRepository:
    if not lifecycle.execution_repo:
        raise HTTPException(500, "ExecutionRepository not initialized")
    return lifecycle.execution_repo


# Type aliases for repositories
ScheduleRepoDep = Annotated[ScheduleRepository, Depends(get_schedule_repository)]
ExecutionRepoDep = Annotated[ExecutionRepository, Depends(get_execution_repository)]


# --------------------------- domain services ------------------------------- #
def get_schedule_service(lifecycle: LifecycleDep) -> ScheduleService:
    if not lifecycle.schedule_service:
        raise HTTPException(500, "ScheduleService not initialized")
    return lifecycle.schedule_service


def get_job_executor(lifecycle: LifecycleDep) -> JobExecutor:
    if not lifecycle.job_executor:
        raise HTTPException(500, "JobExecutor not initialized")
    return lifecycle.job_executor


def get_scheduler_manager(lifecycle: LifecycleDep) -> SchedulerManager:
    if not lifecycle.scheduler_manager:
        raise HTTPException(500, "SchedulerManager not initialized")
    return lifecycle.scheduler_manager


# Type aliases for domain services
ScheduleServiceDep = Annotated[ScheduleService, Depends(get_schedule_service)]
JobExecutorDep = Annotated[JobExecutor, Depends(get_job_executor)]
SchedulerManagerDep = Annotated[SchedulerManager, Depends(get_scheduler_manager)]