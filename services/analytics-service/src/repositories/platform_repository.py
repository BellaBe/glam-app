from shared.database import Repository
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import Optional, List, Dict, Any
from datetime import date, timedelta
from decimal import Decimal
from ..models.analytics import PlatformMetrics

class PlatformMetricsRepository(Repository[PlatformMetrics]):
    """Repository for platform-wide metrics"""
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        super().__init__(PlatformMetrics, session_factory)
    
    async def find_by_date(self, target_date: date) -> Optional[PlatformMetrics]:
        """Find platform metrics by date"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                self.model_cls.date == target_date
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_date_range(self, start_date: date, end_date: date) -> List[PlatformMetrics]:
        """Get platform metrics for date range"""
        async for session in self._session():
            stmt = select(self.model_cls).where(
                and_(
                    self.model_cls.date >= start_date,
                    self.model_cls.date <= end_date
                )
            ).order_by(self.model_cls.date)
            result = await session.execute(stmt)
            return result.scalars().all()
    
    async def get_growth_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Calculate platform growth metrics"""
        async for session in self._session():
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get current and previous period metrics
            current_stmt = select(self.model_cls).where(
                self.model_cls.date == end_date
            )
            previous_stmt = select(self.model_cls).where(
                self.model_cls.date == start_date
            )
            
            current_result = await session.execute(current_stmt)
            previous_result = await session.execute(previous_stmt)
            
            current = current_result.scalar_one_or_none()
            previous = previous_result.scalar_one_or_none()
            
            if not current or not previous:
                return {}
            
            def calculate_growth(current_val, previous_val):
                if previous_val == 0:
                    return 100.0 if current_val > 0 else 0.0
                return ((current_val - previous_val) / previous_val) * 100
            
            return {
                'merchant_growth': calculate_growth(
                    current.total_merchants, 
                    previous.total_merchants
                ),
                'revenue_growth': calculate_growth(
                    current.revenue, 
                    previous.revenue
                ),
                'usage_growth': calculate_growth(
                    current.total_credits_consumed,
                    previous.total_credits_consumed
                ),
                'api_growth': calculate_growth(
                    current.total_api_calls,
                    previous.total_api_calls
                ),
                'period_days': days,
                'current_date': end_date,
                'comparison_date': start_date
            }
    
    async def get_aggregated_metrics(self, months: int = 12) -> Dict[str, Any]:
        """Get aggregated metrics over time period"""
        async for session in self._session():
            end_date = date.today()
            start_date = end_date - timedelta(days=months * 30)
            
            stmt = select(
                func.sum(self.model_cls.revenue).label('total_revenue'),
                func.avg(self.model_cls.total_merchants).label('avg_merchants'),
                func.sum(self.model_cls.total_credits_consumed).label('total_credits'),
                func.sum(self.model_cls.total_api_calls).label('total_api_calls'),
                func.avg(self.model_cls.platform_uptime).label('avg_uptime')
            ).where(
                and_(
                    self.model_cls.date >= start_date,
                    self.model_cls.date <= end_date
                )
            )
            
            result = await session.execute(stmt)
            row = result.first()
            
            return {
                'total_revenue': row.total_revenue or 0,
                'avg_merchants': row.avg_merchants or 0,
                'total_credits': row.total_credits or 0,
                'total_api_calls': row.total_api_calls or 0,
                'avg_uptime': row.avg_uptime or 0,
                'period_months': months
            }


