from shared.database import Repository
from sqlalchemy import select, and_, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from ..models.analytics import AlertRule, AlertHistory
from ..models.enums import AlertType, AlertSeverity, AlertStatus

class AlertRuleRepository(Repository[AlertRule]):
    """Repository for alert rules"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(AlertRule, session_factory)
    
    async def find_active_rules(self, merchant_id: Optional[UUID] = None) -> List[AlertRule]:
        """Find active alert rules"""
        async for session in self._session():
            conditions = [self.model_cls.is_active == True]
            if merchant_id:
                conditions.append(
                    or_(
                        self.model_cls.merchant_id == merchant_id,
                        self.model_cls.merchant_id.is_(None)  # Platform-wide rules
                    )
                )
            
            stmt = select(self.model_cls).where(and_(*conditions))
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def find_by_merchant_and_type(
        self, 
        merchant_id: UUID, 
        alert_type: AlertType
    ) -> List[AlertRule]:
        """Find alert rules by merchant and type"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    or_(
                        self.model_cls.merchant_id == merchant_id,
                        self.model_cls.merchant_id.is_(None)
                    ),
                    self.model_cls.alert_type == alert_type,
                    self.model_cls.is_active == True
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def check_cooldown(self, rule_id: UUID, cooldown_minutes: int) -> bool:
        """Check if rule is in cooldown period"""
        async for session in self._session():
            cutoff_time = datetime.utcnow() - timedelta(minutes=cooldown_minutes)
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.id == rule_id,
                    self.model_cls.last_triggered > cutoff_time
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

class AlertHistoryRepository(Repository[AlertHistory]):
    """Repository for alert history"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(AlertHistory, session_factory)
    
    async def find_by_merchant(
        self, 
        merchant_id: UUID, 
        status: Optional[AlertStatus] = None,
        limit: int = 50
    ) -> List[AlertHistory]:
        """Find alert history by merchant"""
        async for session in self._session():
            conditions = [self.model_cls.merchant_id == merchant_id]
            if status:
                conditions.append(self.model_cls.status == status)
            
            stmt = select(self.model_cls).where(
                and_(*conditions)
            ).order_by(desc(self.model_cls.triggered_at)).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def find_active_alerts(self, merchant_id: UUID) -> List[AlertHistory]:
        """Find active (unresolved) alerts"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.status == AlertStatus.ACTIVE
                )
            ).order_by(desc(self.model_cls.triggered_at))
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def count_daily_alerts(self, rule_id: UUID, target_date: datetime) -> int:
        """Count alerts triggered for a rule on a specific date"""
        async for session in self._session():
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            stmt = select(func.count(self.model_cls.id)).where(
                and_(
                    self.model_cls.alert_rule_id == rule_id,
                    self.model_cls.triggered_at >= start_of_day,
                    self.model_cls.triggered_at < end_of_day
                )
            )
            result = await session.execute(stmt)
            return result.scalar() or 0
    
    async def find_by_rule_and_status(
        self, 
        rule_id: UUID, 
        status: AlertStatus
    ) -> List[AlertHistory]:
        """Find alerts by rule and status"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.alert_rule_id == rule_id,
                    self.model_cls.status == status
                )
            ).order_by(desc(self.model_cls.triggered_at))
            result = await session.execute(stmt)
            return result.scalars().all()


