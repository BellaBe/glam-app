# services/scheduler-service/src/routers/__init__.py
from . import health, schedules, executions

__all__ = ['health', 'schedules', 'executions']