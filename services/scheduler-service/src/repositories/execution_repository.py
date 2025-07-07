# services/scheduler-service/src/repositories/execution_repository.py
"""Repository for execution operations"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, update, desc
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models.execution import ScheduleExecution, ExecutionStatus


class ExecutionRepository(BaseRepository[ScheduleExecution]):
    """Repository for execution database operations"""
    
    def __init__(self, db_manager):
        super().__init__(ScheduleExecution, db_manager)
    
    async def get_by_schedule(
        self,
        schedule_id: UUID,
        offset: int = 0,
        limit: int = 100,
        status: Optional[ExecutionStatus] = None
    ) -> List[ScheduleExecution]:
        """Get executions for a schedule"""
        filters = [ScheduleExecution.schedule_id == schedule_id]
        if status:
            filters.append(ScheduleExecution.status == status)
        
        async for session in self._session():
            result = await session.execute(
                select(ScheduleExecution)
                .where(and_(*filters))
                .order_by(desc(ScheduleExecution.scheduled_for))
                .offset(offset)
                .limit(limit)
            )
            return list(result.scalars().all())
    
    async def get_running_executions(
        self,
        schedule_id: Optional[UUID] = None
    ) -> List[ScheduleExecution]:
        """Get currently running executions"""
        filters = [ScheduleExecution.status == ExecutionStatus.RUNNING]
        if schedule_id:
            filters.append(ScheduleExecution.schedule_id == schedule_id)
        
        return await self.get_all(filters=filters)
    
    async def get_by_correlation_id(
        self,
        correlation_id: str
    ) -> Optional[ScheduleExecution]:
        """Get execution by correlation ID"""
        async for session in self._session():
            result = await session.execute(
                select(ScheduleExecution).where(
                    ScheduleExecution.correlation_id == correlation_id
                )
            )
            return result.scalar_one_or_none()
    
    async def update_status(
        self,
        execution_id: UUID,
        status: ExecutionStatus,
        **kwargs
    ) -> bool:
        """Update execution status"""
        async for session in self._session():
            values = {'status': status}
            
            if status == ExecutionStatus.RUNNING:
                values['started_at'] = datetime.utcnow()
            elif status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]:
                values['completed_at'] = datetime.utcnow()
            
            values.update(kwargs)
            
            result = await session.execute(
                update(ScheduleExecution)
                .where(ScheduleExecution.id == execution_id)
                .values(**values)
            )
            await session.commit()
            return result.rowcount > 0
    
    async def get_stats(
        self,
        schedule_id: UUID,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Get execution statistics for a schedule"""
        async for session in self._session():
            base_query = select(ScheduleExecution).where(
                ScheduleExecution.schedule_id == schedule_id
            )
            
            if time_window:
                cutoff = datetime.utcnow() - time_window
                base_query = base_query.where(
                    ScheduleExecution.scheduled_for >= cutoff
                )
            
            # Get status counts
            status_counts = await session.execute(
                select(
                    ScheduleExecution.status,
                    func.count(ScheduleExecution.id).label('count')
                ).where(
                    ScheduleExecution.schedule_id == schedule_id
                ).group_by(ScheduleExecution.status)
            )
            
            counts = {row.status: row.count for row in status_counts}
            
            # Get duration stats for successful executions
            duration_stats = await session.execute(
                select(
                    func.avg(ScheduleExecution.duration_ms).label('avg'),
                    func.min(ScheduleExecution.duration_ms).label('min'),
                    func.max(ScheduleExecution.duration_ms).label('max')
                ).where(
                    and_(
                        ScheduleExecution.schedule_id == schedule_id,
                        ScheduleExecution.status == ExecutionStatus.SUCCESS,
                        ScheduleExecution.duration_ms.isnot(None)
                    )
                )
            )
            
            duration_row = duration_stats.one()
            
            # Get last execution
            last_execution = await session.execute(
                select(ScheduleExecution.completed_at)
                .where(
                    and_(
                        ScheduleExecution.schedule_id == schedule_id,
                        ScheduleExecution.status.in_([
                            ExecutionStatus.SUCCESS,
                            ExecutionStatus.FAILED
                        ])
                    )
                ).order_by(desc(ScheduleExecution.completed_at))
                .limit(1)
            )
            
            last_at = last_execution.scalar()
            
            # Get consecutive failures
            consecutive_failures = await self._get_consecutive_failures(
                session, schedule_id
            )
            
            total = sum(counts.values())
            success_rate = counts.get(ExecutionStatus.SUCCESS, 0) / total if total > 0 else 0
            
            return {
                'total_executions': total,
                'successful_executions': counts.get(ExecutionStatus.SUCCESS, 0),
                'failed_executions': counts.get(ExecutionStatus.FAILED, 0),
                'skipped_executions': counts.get(ExecutionStatus.SKIPPED, 0),
                'average_duration_ms': duration_row.avg,
                'min_duration_ms': duration_row.min,
                'max_duration_ms': duration_row.max,
                'last_execution_at': last_at,
                'success_rate': success_rate,
                'consecutive_failures': consecutive_failures
            }
    
    async def _get_consecutive_failures(
        self,
        session: AsyncSession,
        schedule_id: UUID
    ) -> int:
        """Get count of consecutive failures"""
        # Get the most recent executions ordered by time
        result = await session.execute(
            select(ScheduleExecution.status)
            .where(ScheduleExecution.schedule_id == schedule_id)
            .order_by(desc(ScheduleExecution.scheduled_for))
            .limit(100)  # Reasonable limit
        )
        
        consecutive = 0
        for row in result:
            if row.status == ExecutionStatus.FAILED:
                consecutive += 1
            else:
                break
        
        return consecutive
    
    async def cleanup_old_executions(
        self,
        older_than: datetime,
        batch_size: int = 1000
    ) -> int:
        """Delete old execution records"""
        async for session in self._session():
            total_deleted = 0
            
            while True:
                # Get IDs to delete
                result = await session.execute(
                    select(ScheduleExecution.id)
                    .where(ScheduleExecution.completed_at < older_than)
                    .limit(batch_size)
                )
                
                ids_to_delete = [row.id for row in result]
                
                if not ids_to_delete:
                    break
                
                # Delete batch
                await session.execute(
                    delete(ScheduleExecution)
                    .where(ScheduleExecution.id.in_(ids_to_delete))
                )
                
                await session.commit()
                total_deleted += len(ids_to_delete)
            
            return total_deleted