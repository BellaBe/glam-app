# services/scheduler-service/src/lifecycle.py
"""
Process-wide lifecycle manager for the Scheduler Service.

Responsible for:
- Initializing all service components
- Managing startup/shutdown sequence
- Handling graceful shutdown
- Managing background tasks
"""

import asyncio
from typing import Optional, List

from shared.utils.logger import create_logger, ServiceLogger
from shared.messaging import JetStreamWrapper, StreamConfig
from shared.database import DatabaseSessionManager
from shared.messaging.publisher import JetStreamEventPublisher

from .config import ServiceConfig
from .repositories import ScheduleRepository, ExecutionRepository
from .mappers import ScheduleMapper, ExecutionMapper
from .services import ScheduleService, JobExecutor, SchedulerManager
from .events import SchedulerEventPublisher
from .events.subscribers import (
    CreateScheduleSubscriber,
    UpdateScheduleSubscriber,
    DeleteScheduleSubscriber,
    PauseScheduleSubscriber,
    ResumeScheduleSubscriber,
    TriggerScheduleSubscriber,
    ExecuteImmediateSubscriber
)
from .utils import DistributedLock, create_scheduler_callback


class ServiceLifecycle:
    """Manages the lifecycle of all service components"""

    def __init__(self, config: ServiceConfig) -> None:
        self.config = config
        self.logger: ServiceLogger = create_logger(config.SERVICE_NAME)

        # External connections
        self.messaging_wrapper: Optional[JetStreamWrapper] = None
        self.db_manager: Optional[DatabaseSessionManager] = None
        self.distributed_lock: Optional[DistributedLock] = None

        # Repositories
        self.schedule_repo: Optional[ScheduleRepository] = None
        self.execution_repo: Optional[ExecutionRepository] = None

        # Mappers
        self.schedule_mapper: Optional[ScheduleMapper] = None
        self.execution_mapper: Optional[ExecutionMapper] = None

        # Services
        self.scheduler_manager: Optional[SchedulerManager] = None
        self.job_executor: Optional[JobExecutor] = None
        self.schedule_service: Optional[ScheduleService] = None

        # Publishers
        self.base_publisher: Optional[JetStreamEventPublisher] = None

        # Bookkeeping
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

    # ─────────────────────────── FastAPI lifespan hooks ────────────────────
    async def startup(self) -> None:
        try:
            await self._init_messaging()
            await self._init_database()
            await self._init_distributed_lock()
            self._init_repositories()
            self._init_mappers()
            await self._init_services()
            await self._start_subscribers()
            await self._start_scheduler()
            self.logger.info("%s started successfully", self.config.SERVICE_NAME)
        except Exception:
            self.logger.critical("Service failed to start")
            await self.shutdown()
            raise

    async def shutdown(self) -> None:
        self.logger.info("Shutting down %s", self.config.SERVICE_NAME)

        # Cancel all tasks
        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        # Stop scheduler
        if self.scheduler_manager:
            await self.scheduler_manager.stop()

        # Close connections
        if self.distributed_lock:
            await self.distributed_lock.disconnect()
        if self.messaging_wrapper:
            await self.messaging_wrapper.close()
        if self.db_manager:
            await self.db_manager.close()

        self.logger.info("%s shutdown complete", self.config.SERVICE_NAME)

    # ───────────────────────────── init helpers ────────────────────────────
    async def _init_messaging(self) -> None:
        self.messaging_wrapper = JetStreamWrapper(self.logger)
        await self.messaging_wrapper.connect(self.config.NATS_SERVERS)
        self.logger.info("Connected to NATS %s", self.config.NATS_SERVERS)

        js = self.messaging_wrapper.js
        cfg = StreamConfig(
            name="SCHEDULER",
            subjects=["cmd.scheduler.*", "evt.scheduler.*"],
            retention="limits",
            max_msgs=1_000_000,
            max_age=30 * 24 * 60 * 60,  # 30 days
            max_msg_size=1024 * 1024,  # 1MB
            storage="file",
            replicas=1,
            discard="old"
        )
        await self.messaging_wrapper.ensure_stream(cfg)

        # Initialize publishers
        await self.messaging_wrapper.init_publishers([SchedulerEventPublisher])

        # Get base publisher for sending commands to other services
        self.base_publisher = JetStreamEventPublisher(
            self.messaging_wrapper.client,
            self.messaging_wrapper.js,
            self.logger
        )

    async def _init_database(self) -> None:
        self.db_manager = DatabaseSessionManager(
            database_url=self.config.DATABASE_URL,
            echo=self.config.DEBUG
        )
        await self.db_manager.init()
        self.logger.info("Database initialized")

    async def _init_distributed_lock(self) -> None:
        self.distributed_lock = DistributedLock(
            redis_url=self.config.REDIS_URL,
            logger=self.logger
        )
        await self.distributed_lock.connect()
        self.logger.info("Distributed lock initialized")

    def _init_repositories(self) -> None:
        if not self.db_manager:
            raise RuntimeError("Database manager is not initialized")

        self.schedule_repo = ScheduleRepository(self.db_manager)
        self.execution_repo = ExecutionRepository(self.db_manager)

    def _init_mappers(self) -> None:
        self.schedule_mapper = ScheduleMapper()
        self.execution_mapper = ExecutionMapper()

    async def _init_services(self) -> None:
        if not all([
            self.messaging_wrapper,
            self.schedule_repo,
            self.execution_repo,
            self.distributed_lock,
            self.base_publisher
        ]):
            raise RuntimeError("Required dependencies not initialized")

        # Get event publisher
        publisher = self.messaging_wrapper.get_publisher(SchedulerEventPublisher)
        if not publisher:
            raise RuntimeError("SchedulerEventPublisher is not initialized")

        # Create job executor first (needed by scheduler manager)
        self.job_executor = JobExecutor(
            config=self.config,
            schedule_repo=self.schedule_repo,
            execution_repo=self.execution_repo,
            base_publisher=self.base_publisher,
            event_publisher=publisher,
            distributed_lock=self.distributed_lock,
            logger=self.logger
        )

        # Create scheduler manager with callback
        callback = create_scheduler_callback(self.job_executor)
        self.scheduler_manager = SchedulerManager(
            config=self.config,
            job_callback=callback,
            logger=self.logger
        )

        # Create schedule service
        self.schedule_service = ScheduleService(
            config=self.config,
            schedule_repo=self.schedule_repo,
            schedule_mapper=self.schedule_mapper,
            event_publisher=publisher,
            scheduler_manager=self.scheduler_manager,
            logger=self.logger
        )

    async def _start_subscribers(self) -> None:
        if not self.messaging_wrapper:
            raise RuntimeError("Messaging wrapper is not initialized")

        # Initialize subscribers
        subscribers = [
            CreateScheduleSubscriber,
            UpdateScheduleSubscriber,
            DeleteScheduleSubscriber,
            PauseScheduleSubscriber,
            ResumeScheduleSubscriber,
            TriggerScheduleSubscriber,
            ExecuteImmediateSubscriber
        ]

        # Inject dependencies into subscribers
        for sub_cls in subscribers:
            subscriber = sub_cls()
            if hasattr(subscriber, 'set_schedule_service'):
                subscriber.set_schedule_service(self.schedule_service)
            if hasattr(subscriber, 'set_job_executor'):
                subscriber.set_job_executor(self.job_executor)
            if hasattr(subscriber, 'set_base_publisher'):
                subscriber.set_base_publisher(self.base_publisher)
            
            await self.messaging_wrapper.start_subscriber(sub_cls)

    async def _start_scheduler(self) -> None:
        """Start the APScheduler"""
        if not self.scheduler_manager:
            raise RuntimeError("Scheduler manager is not initialized")

        await self.scheduler_manager.start()

        # Load existing active schedules
        await self._load_existing_schedules()

    async def _load_existing_schedules(self) -> None:
        """Load existing schedules into APScheduler on startup"""
        if not all([self.schedule_repo, self.scheduler_manager]):
            return

        try:
            # Get all active schedules
            schedules = await self.schedule_repo.get_active_schedules(limit=1000)
            
            self.logger.info(f"Loading {len(schedules)} active schedules")
            
            for schedule in schedules:
                try:
                    job_id = self.scheduler_manager.add_schedule(schedule)
                    schedule.job_id = job_id
                    await self.schedule_repo.update(schedule)
                except Exception as e:
                    self.logger.error(
                        f"Failed to load schedule: {schedule.id}",
                        extra={
                            "schedule_id": str(schedule.id),
                            "error": str(e)
                        }
                    )
            
            self.logger.info("Finished loading existing schedules")
            
        except Exception as e:
            self.logger.error(
                "Failed to load existing schedules",
                extra={"error": str(e)}
            )

    # ──────────────────────────── convenience tools ───────────────────────
    def add_task(self, coro) -> asyncio.Task:
        t = asyncio.create_task(coro)
        self._tasks.append(t)
        return t

    async def wait_for_shutdown(self) -> None:
        await self._shutdown_event.wait()

    def signal_shutdown(self) -> None:
        self._shutdown_event.set()