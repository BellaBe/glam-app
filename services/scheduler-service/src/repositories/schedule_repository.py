# services/scheduler-service/src/repositories/schedule_repository.py
"""Repository for schedule operations"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from ..models.schedule import Schedule, ScheduleStatus, ScheduleType


class ScheduleRepository(BaseRepository[Schedule]):
    """Repository for schedule database operations"""
    
    def __init__(self, db_manager):
        super().__init__(Schedule, db_manager)
    
    async def get_by_name_and_creator(
        self,
        name: str,
        created_by: str
    ) -> Optional[Schedule]:
        """Get schedule by name and creator"""
        async for session in self._session():
            result = await session.execute(
                select(Schedule).where(
                    and_(
                        Schedule.name == name,
                        Schedule.created_by == created_by,
                        Schedule.deleted_at.is_(None)
                    )
                )
            )
            return result.scalar_one_or_none()
    
    async def get_active_schedules(
        self,
        offset: int = 0,
        limit: int = 100
    ) -> List[Schedule]:
        """Get all active schedules"""
        filters = [
            Schedule.status == ScheduleStatus.ACTIVE,
            Schedule.is_active == True,
            Schedule.is_paused == False,
            Schedule.deleted_at.is_(None)
        ]
        return await self.get_all(offset, limit, filters)
    
    async def get_schedules_to_run(
        self,
        before: datetime,
        limit: int = 100
    ) -> List[Schedule]:
        """Get schedules that need to run before specified time"""
        async for session in self._session():
            result = await session.execute(
                select(Schedule).where(
                    and_(
                        Schedule.status == ScheduleStatus.ACTIVE,
                        Schedule.is_active == True,
                        Schedule.is_paused == False,
                        Schedule.next_run_at <= before,
                        Schedule.deleted_at.is_(None)
                    )
                ).order_by(Schedule.next_run_at).limit(limit)
            )
            return list(result.scalars().all())
    
    async def get_by_job_id(self, job_id: str) -> Optional[Schedule]:
        """Get schedule by APScheduler job ID"""
        async for session in self._session():
            result = await session.execute(
                select(Schedule).where(Schedule.job_id == job_id)
            )
            return result.scalar_one_or_none()
    
    async def get_by_tags(
        self,
        tags: List[str],
        offset: int = 0,
        limit: int = 100
    ) -> List[Schedule]:
        """Get schedules by tags"""
        async for session in self._session():
            # PostgreSQL JSON containment operator
            result = await session.execute(
                select(Schedule).where(
                    and_(
                        Schedule.tags.contains(tags),
                        Schedule.deleted_at.is_(None)
                    )
                ).offset(offset).limit(limit)
            )
            return list(result.scalars().all())
    
    async def get_by_creator(
        self,
        created_by: str,
        offset: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Schedule]:
        """Get schedules by creator"""
        filters = [Schedule.created_by == created_by]
        if not include_deleted:
            filters.append(Schedule.deleted_at.is_(None))
        
        return await self.get_all(offset, limit, filters)
    
    async def count_by_creator(
        self,
        created_by: str,
        include_deleted: bool = False
    ) -> int:
        """Count schedules by creator"""
        filters = [Schedule.created_by == created_by]
        if not include_deleted:
            filters.append(Schedule.deleted_at.is_(None))
        
        return await self.count(filters)
    
    async def soft_delete(
        self,
        schedule_id: UUID,
        deleted_by: str
    ) -> bool:
        """Soft delete a schedule"""
        async for session in self._session():
            result = await session.execute(
                update(Schedule)
                .where(Schedule.id == schedule_id)
                .values(
                    status=ScheduleStatus.DELETED,
                    is_active=False,
                    deleted_at=datetime.utcnow(),
                    deleted_by=deleted_by
                )
            )
            await session.commit()
            return result.rowcount > 0
    
    async def update_last_run(
        self,
        schedule_id: UUID,
        last_run_at: datetime,
        next_run_at: Optional[datetime] = None,
        increment_success: bool = True
    ) -> bool:
        """Update schedule after successful execution"""
        async for session in self._session():
            values = {
                'last_run_at': last_run_at,
                'run_count': Schedule.run_count + 1
            }
            
            if next_run_at:
                values['next_run_at'] = next_run_at
            
            if increment_success:
                values['success_count'] = Schedule.success_count + 1
            else:
                values['failure_count'] = Schedule.failure_count + 1
            
            result = await session.execute(
                update(Schedule)
                .where(Schedule.id == schedule_id)
                .values(**values)
            )
            await session.commit()
            return result.rowcount > 0
    
    async def bulk_update_status(
        self,
        schedule_ids: List[UUID],
        status: ScheduleStatus,
        **kwargs
    ) -> int:
        """Bulk update schedule status"""
        async for session in self._session():
            values = {'status': status, 'updated_at': datetime.utcnow()}
            values.update(kwargs)
            
            result = await session.execute(
                update(Schedule)
                .where(Schedule.id.in_(schedule_ids))
                .values(**values)
            )
            await session.commit()
            return result.rowcount
    
    async def get_stats_by_type(self) -> Dict[str, int]:
        """Get schedule counts by type"""
        async for session in self._session():
            result = await session.execute(
                select(
                    Schedule.schedule_type,
                    func.count(Schedule.id).label('count')
                ).where(
                    Schedule.deleted_at.is_(None)
                ).group_by(Schedule.schedule_type)
            )
            return {row.schedule_type: row.count for row in result}

