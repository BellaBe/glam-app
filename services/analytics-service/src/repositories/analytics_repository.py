from shared.database import Repository
from sqlalchemy import select, and_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import date, datetime, timedelta
from decimal import Decimal
from ..models.analytics import (
    UsageAnalytics, OrderAnalytics, LifecycleTrialAnalytics,
    UsagePattern, PredictionModel, EngagementMetric, ShopifyAnalytics
)
from ..models.enums import PatternType, PredictionType, EngagementPeriod

class AnalyticsRepository(Repository[UsageAnalytics]):
    """Repository for analytics operations"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(UsageAnalytics, session_factory)
    
    async def find_by_merchant_and_date(self, merchant_id: UUID, target_date: date) -> Optional[UsageAnalytics]:
        """Find usage analytics by merchant and date"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.date == target_date
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_usage_trends(
        self, 
        merchant_id: UUID, 
        start_date: date, 
        end_date: date
    ) -> List[UsageAnalytics]:
        """Get usage analytics within date range"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.date >= start_date,
                    self.model_cls.date <= end_date
                )
            ).order_by(self.model_cls.date)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_daily_aggregates(
        self,
        merchant_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get aggregated daily metrics"""
        async for session in self._session():
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            stmt = select(
                func.sum(self.model_cls.total_credits_consumed).label('total_credits'),
                func.sum(self.model_cls.api_calls).label('total_api_calls'),
                func.avg(self.model_cls.unique_users).label('avg_users'),
                func.avg(self.model_cls.average_response_time_ms).label('avg_response_time')
            ).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.date >= start_date,
                    self.model_cls.date <= end_date
                )
            )
            result = await session.execute(stmt)
            row = result.first()
            
            return {
                'total_credits': row.total_credits or 0,
                'total_api_calls': row.total_api_calls or 0,
                'avg_users': row.avg_users or 0,
                'avg_response_time': row.avg_response_time or 0,
                'period_days': days
            }

class OrderAnalyticsRepository(Repository[OrderAnalytics]):
    """Repository for order analytics"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(OrderAnalytics, session_factory)
    
    async def find_by_merchant_and_date(self, merchant_id: UUID, target_date: date) -> Optional[OrderAnalytics]:
        """Find order analytics by merchant and date"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.date == target_date
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_depletion_forecasts(self, merchant_id: UUID) -> List[OrderAnalytics]:
        """Get recent order analytics for depletion forecasting"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.projected_depletion_date.isnot(None)
                )
            ).order_by(desc(self.model_cls.date)).limit(30)
            result = await session.execute(stmt)
            return result.scalars().all()

class LifecycleTrialAnalyticsRepository(Repository[LifecycleTrialAnalytics]):
    """Repository for trial analytics"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(LifecycleTrialAnalytics, session_factory)
    
    async def find_by_merchant(self, merchant_id: UUID) -> Optional[LifecycleTrialAnalytics]:
        """Find trial analytics by merchant"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                self.model_cls.merchant_id == merchant_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def find_active_trials(self) -> List[LifecycleTrialAnalytics]:
        """Find all active trials"""
        async for session in self._session():
            now = datetime.utcnow()
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.trial_end_date > now,
                    self.model_cls.converted == False
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()

class UsagePatternRepository(Repository[UsagePattern]):
    """Repository for usage patterns"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(UsagePattern, session_factory)
    
    async def find_by_merchant_and_type(
        self, 
        merchant_id: UUID, 
        pattern_type: PatternType
    ) -> List[UsagePattern]:
        """Find patterns by merchant and type"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.pattern_type == pattern_type
                )
            ).order_by(desc(self.model_cls.confidence_score))
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def find_valid_patterns(self, merchant_id: UUID) -> List[UsagePattern]:
        """Find currently valid patterns"""
        async for session in self._session():
            now = datetime.utcnow()
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    func.coalesce(self.model_cls.valid_until, now + timedelta(days=1)) > now
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()

class PredictionModelRepository(Repository[PredictionModel]):
    """Repository for prediction models"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(PredictionModel, session_factory)
    
    async def find_by_merchant_and_type(
        self,
        merchant_id: UUID,
        prediction_type: PredictionType,
        limit: int = 10
    ) -> List[PredictionModel]:
        """Find predictions by merchant and type"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.prediction_type == prediction_type
                )
            ).order_by(desc(self.model_cls.prediction_date)).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def find_latest_prediction(
        self,
        merchant_id: UUID,
        prediction_type: PredictionType
    ) -> Optional[PredictionModel]:
        """Find latest prediction of type"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.prediction_type == prediction_type
                )
            ).order_by(desc(self.model_cls.prediction_date)).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

class EngagementMetricRepository(Repository[EngagementMetric]):
    """Repository for engagement metrics"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(EngagementMetric, session_factory)
    
    async def find_by_merchant_and_period(
        self,
        merchant_id: UUID,
        period: EngagementPeriod,
        limit: int = 12
    ) -> List[EngagementMetric]:
        """Find engagement metrics by period"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.period == period
                )
            ).order_by(desc(self.model_cls.period_start)).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()

class ShopifyAnalyticsRepository(Repository[ShopifyAnalytics]):
    """Repository for Shopify analytics"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(ShopifyAnalytics, session_factory)
    
    async def find_by_merchant_and_date(
        self, 
        merchant_id: UUID, 
        target_date: date
    ) -> Optional[ShopifyAnalytics]:
        """Find Shopify analytics by merchant and date"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.date == target_date
                )
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_integration_health(self, merchant_id: UUID, days: int = 7) -> Dict[str, Any]:
        """Get integration health metrics"""
        async for session in self._session():
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            stmt = select(
                func.sum(self.model_cls.webhook_events_processed).label('total_webhooks'),
                func.sum(self.model_cls.webhook_events_failed).label('failed_webhooks'),
                func.sum(self.model_cls.api_calls_made).label('total_api_calls'),
                func.sum(self.model_cls.api_calls_failed).label('failed_api_calls'),
                func.sum(self.model_cls.api_rate_limit_hits).label('rate_limit_hits')
            ).where(
                and_(
                    self.model_cls.merchant_id == merchant_id,
                    self.model_cls.date >= start_date,
                    self.model_cls.date <= end_date
                )
            )
            result = await session.execute(stmt)
            row = result.first()
            
            total_webhooks = row.total_webhooks or 0
            failed_webhooks = row.failed_webhooks or 0
            total_api_calls = row.total_api_calls or 0
            failed_api_calls = row.failed_api_calls or 0
            
            webhook_success_rate = (
                (total_webhooks - failed_webhooks) / total_webhooks * 100
                if total_webhooks > 0 else 100
            )
            api_success_rate = (
                (total_api_calls - failed_api_calls) / total_api_calls * 100
                if total_api_calls > 0 else 100
            )
            
            return {
                'webhook_success_rate': webhook_success_rate,
                'api_success_rate': api_success_rate,
                'total_webhooks': total_webhooks,
                'total_api_calls': total_api_calls,
                'rate_limit_hits': row.rate_limit_hits or 0,
                'period_days': days
            }


