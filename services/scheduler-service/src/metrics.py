# services/scheduler-service/src/metrics.py
"""
Scheduler service specific metrics.

This module defines domain-specific metrics for the scheduler service
that extend the standard HTTP metrics from shared.
"""

from prometheus_client import Counter, Histogram, Gauge
from typing import Optional

# Schedule metrics
schedules_total = Gauge(
    'schedules_total',
    'Total number of schedules',
    ['type', 'status']
)

schedules_created_total = Counter(
    'schedules_created_total',
    'Total schedules created',
    ['type', 'creator']
)

schedules_deleted_total = Counter(
    'schedules_deleted_total',
    'Total schedules deleted',
    ['type', 'hard_delete']
)

# Execution metrics
schedule_executions_total = Counter(
    'schedule_executions_total',
    'Total schedule executions',
    ['schedule_type', 'status']
)

schedule_execution_duration_seconds = Histogram(
    'schedule_execution_duration_seconds',
    'Schedule execution duration in seconds',
    ['schedule_type', 'status'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0)
)

schedule_misfires_total = Counter(
    'schedule_misfires_total',
    'Total missed schedule executions',
    ['schedule_type']
)

# Queue metrics
schedule_queue_depth = Gauge(
    'schedule_queue_depth',
    'Number of pending schedule executions'
)

active_executions = Gauge(
    'active_executions',
    'Number of currently running executions'
)

# Lock metrics
distributed_locks_acquired_total = Counter(
    'distributed_locks_acquired_total',
    'Total distributed locks acquired',
    ['lock_type']
)

distributed_locks_failed_total = Counter(
    'distributed_locks_failed_total',
    'Total distributed lock acquisition failures',
    ['lock_type', 'reason']
)

distributed_lock_hold_duration_seconds = Histogram(
    'distributed_lock_hold_duration_seconds',
    'Duration locks are held in seconds',
    ['lock_type']
)

# Retry metrics
schedule_retries_total = Counter(
    'schedule_retries_total',
    'Total schedule execution retries',
    ['schedule_type', 'attempt']
)

# APScheduler metrics
apscheduler_jobs_total = Gauge(
    'apscheduler_jobs_total',
    'Total jobs in APScheduler',
    ['state']
)

# Helper functions for easier metric updates
def increment_schedule_created(schedule_type: str, creator: str):
    """Increment schedule created counter"""
    schedules_created_total.labels(
        type=schedule_type,
        creator=creator
    ).inc()


def increment_schedule_deleted(schedule_type: str, hard_delete: bool):
    """Increment schedule deleted counter"""
    schedules_deleted_total.labels(
        type=schedule_type,
        hard_delete=str(hard_delete)
    ).inc()


def increment_execution(schedule_type: str, status: str):
    """Increment execution counter"""
    schedule_executions_total.labels(
        schedule_type=schedule_type,
        status=status
    ).inc()


def observe_execution_duration(schedule_type: str, status: str, duration_seconds: float):
    """Record execution duration"""
    schedule_execution_duration_seconds.labels(
        schedule_type=schedule_type,
        status=status
    ).observe(duration_seconds)


def increment_misfire(schedule_type: str):
    """Increment misfire counter"""
    schedule_misfires_total.labels(
        schedule_type=schedule_type
    ).inc()


def update_schedule_counts(type_counts: dict, status_counts: dict):
    """Update schedule gauge metrics"""
    # Reset all metrics first
    for schedule_type in ['cron', 'interval', 'one_time', 'immediate']:
        for status in ['active', 'paused', 'completed', 'failed', 'deleted']:
            schedules_total.labels(type=schedule_type, status=status).set(0)
    
    # Update with current values
    for schedule_type, count in type_counts.items():
        for status, status_count in status_counts.items():
            if schedule_type.lower() in ['cron', 'interval', 'one_time', 'immediate']:
                schedules_total.labels(
                    type=schedule_type.lower(),
                    status=status.lower()
                ).set(status_count)


def increment_lock_acquired(lock_type: str = "schedule_execution"):
    """Increment lock acquired counter"""
    distributed_locks_acquired_total.labels(lock_type=lock_type).inc()


def increment_lock_failed(lock_type: str = "schedule_execution", reason: str = "timeout"):
    """Increment lock failed counter"""
    distributed_locks_failed_total.labels(
        lock_type=lock_type,
        reason=reason
    ).inc()


def observe_lock_duration(lock_type: str, duration_seconds: float):
    """Record lock hold duration"""
    distributed_lock_hold_duration_seconds.labels(
        lock_type=lock_type
    ).observe(duration_seconds)


def increment_retry(schedule_type: str, attempt: int):
    """Increment retry counter"""
    schedule_retries_total.labels(
        schedule_type=schedule_type,
        attempt=str(attempt)
    ).inc()