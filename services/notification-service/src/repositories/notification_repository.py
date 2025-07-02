# File: services/notification-service/src/repositories/notification_repository.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from shared.database import Repository
from ..models.entities import Notification

class NotificationRepository(Repository[Notification]):
    """Repository for notification operations"""
    
    def __init__(self, model_class: type[Notification], session: AsyncSession):
        super().__init__(model_class, session)
    
    async def get_by_shop_id(self, shop_id: UUID, limit: int = 100) -> List[Notification]:
        """Get notifications for a shop"""
        stmt = select(self.model).where(
            self.model.shop_id == shop_id
        ).order_by(self.model.created_at.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_status(self, status: str, limit: int = 100) -> List[Notification]:
        """Get notifications by status"""
        stmt = select(self.model).where(
            self.model.status == status
        ).order_by(self.model.created_at.desc()).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_failed_for_retry(self, max_retries: int = 3) -> List[Notification]:
        """Get failed notifications eligible for retry"""
        stmt = select(self.model).where(
            and_(
                self.model.status == "failed",
                self.model.retry_count < max_retries
            )
        ).order_by(self.model.created_at)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count_by_type_and_shop(
        self,
        shop_id: UUID,
        notification_type: str,
        since: Optional[datetime] = None
    ) -> int:
        """Count notifications by type and shop"""
        stmt = select(func.count(self.model.id)).where(
            and_(
                self.model.shop_id == shop_id,
                self.model.type == notification_type
            )
        )
        
        if since:
            stmt = stmt.where(self.model.created_at >= since)
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def get_stats(self, shop_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get notification statistics"""
        base_query = select(
            self.model.status,
            func.count(self.model.id).label('count')
        )
        
        if shop_id:
            base_query = base_query.where(self.model.shop_id == shop_id)
        
        base_query = base_query.group_by(self.model.status)
        
        result = await self.session.execute(base_query)
        stats = {row.status: row.count for row in result}
        
        # Get type breakdown
        type_query = select(
            self.model.type,
            func.count(self.model.id).label('count')
        )
        
        if shop_id:
            type_query = type_query.where(self.model.shop_id == shop_id)
        
        type_query = type_query.group_by(self.model.type)
        
        type_result = await self.session.execute(type_query)
        type_stats = {row.type: row.count for row in type_result}
        
        return {
            "by_status": stats,
            "by_type": type_stats,
            "total": sum(int(value) for value in stats.values() if isinstance(value, (int, float)))
        }