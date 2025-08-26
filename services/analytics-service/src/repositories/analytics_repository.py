# services/analytics/src/repositories/analytics_repository.py
"""Repository for raw analytics event storage and retrieval"""

from uuid import UUID
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from prisma import Prisma
from prisma.models import AnalyticsEvent, ShopperAnalysis, MatchMetrics
from ..exceptions import DataConsistencyError

class AnalyticsRepository:
    """Repository for analytics event operations"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def create_event(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        platform_domain: str,
        event_type: str,
        event_data: dict,
        shopper_id: Optional[str] = None,
        anonymous_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        match_id: Optional[str] = None
    ) -> AnalyticsEvent:
        """Create a raw analytics event"""
        return await self.prisma.analyticsevent.create(
            data={
                "merchant_id": str(merchant_id),
                "platform_name": platform_name,
                "platform_shop_id": platform_shop_id,
                "platform_domain": platform_domain,
                "event_type": event_type,
                "event_data": event_data,
                "shopper_id": shopper_id,
                "anonymous_id": anonymous_id,
                "analysis_id": analysis_id,
                "match_id": match_id
            }
        )
    
    async def create_shopper_analysis(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        platform_domain: str,
        shopper_id: Optional[str],
        anonymous_id: Optional[str],
        analysis_id: str,
        primary_season: str,
        secondary_season: Optional[str],
        tertiary_season: Optional[str],
        confidence: float,
        processing_time_ms: int
    ) -> ShopperAnalysis:
        """Create shopper analysis record"""
        # Check for duplicate analysis_id
        existing = await self.prisma.shopperanalysis.find_unique(
            where={"analysis_id": analysis_id}
        )
        
        if existing:
            raise DataConsistencyError(
                entity="ShopperAnalysis",
                expected="unique analysis_id",
                actual=f"duplicate analysis_id: {analysis_id}"
            )
        
        return await self.prisma.shopperanalysis.create(
            data={
                "merchant_id": str(merchant_id),
                "platform_name": platform_name,
                "platform_shop_id": platform_shop_id,
                "platform_domain": platform_domain,
                "shopper_id": shopper_id,
                "anonymous_id": anonymous_id,
                "analysis_id": analysis_id,
                "primary_season": primary_season,
                "secondary_season": secondary_season,
                "tertiary_season": tertiary_season,
                "confidence": confidence,
                "processing_time_ms": processing_time_ms
            }
        )
    
    async def create_match_metrics(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_shop_id: str,
        platform_domain: str,
        match_id: str,
        shopper_id: Optional[str],
        anonymous_id: Optional[str],
        analysis_id: str,
        total_matches: int,
        products_matched: List[str],
        avg_match_score: float,
        top_match_score: float,
        primary_season: str,
        credits_consumed: int
    ) -> MatchMetrics:
        """Create match metrics record"""
        # Check for duplicate match_id
        existing = await self.prisma.matchmetrics.find_unique(
            where={"match_id": match_id}
        )
        
        if existing:
            raise DataConsistencyError(
                entity="MatchMetrics",
                expected="unique match_id",
                actual=f"duplicate match_id: {match_id}"
            )
        
        return await self.prisma.matchmetrics.create(
            data={
                "merchant_id": str(merchant_id),
                "platform_name": platform_name,
                "platform_shop_id": platform_shop_id,
                "platform_domain": platform_domain,
                "match_id": match_id,
                "shopper_id": shopper_id,
                "anonymous_id": anonymous_id,
                "analysis_id": analysis_id,
                "total_matches": total_matches,
                "products_matched": products_matched,
                "avg_match_score": avg_match_score,
                "top_match_score": top_match_score,
                "primary_season": primary_season,
                "credits_consumed": credits_consumed
            }
        )
    
    async def get_events_by_merchant(
        self,
        merchant_id: UUID,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AnalyticsEvent]:
        """Get analytics events for a merchant"""
        where_clause = {"merchant_id": str(merchant_id)}
        
        if event_type:
            where_clause["event_type"] = event_type
        
        if start_date or end_date:
            where_clause["event_timestamp"] = {}
            if start_date:
                where_clause["event_timestamp"]["gte"] = start_date
            if end_date:
                where_clause["event_timestamp"]["lte"] = end_date
        
        return await self.prisma.analyticsevent.find_many(
            where=where_clause,
            order_by={"event_timestamp": "desc"},
            take=limit
        )
    
    async def count_analyses_by_merchant(
        self,
        merchant_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Count shopper analyses for a merchant in date range"""
        return await self.prisma.shopperanalysis.count(
            where={
                "merchant_id": str(merchant_id),
                "created_at": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        )
    
    async def count_unique_shoppers(
        self,
        merchant_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Count unique shoppers (by shopper_id or anonymous_id)"""
        # Get all analyses in date range
        analyses = await self.prisma.shopperanalysis.find_many(
            where={
                "merchant_id": str(merchant_id),
                "created_at": {
                    "gte": start_date,
                    "lte": end_date
                }
            },
            select={
                "shopper_id": True,
                "anonymous_id": True
            }
        )
        
        # Count unique identifiers
        unique_ids = set()
        for analysis in analyses:
            if analysis.shopper_id:
                unique_ids.add(f"shopper:{analysis.shopper_id}")
            elif analysis.anonymous_id:
                unique_ids.add(f"anon:{analysis.anonymous_id}")
        
        return len(unique_ids)
    
    async def get_season_distribution(
        self,
        merchant_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """Get distribution of primary seasons"""
        analyses = await self.prisma.shopperanalysis.find_many(
            where={
                "merchant_id": str(merchant_id),
                "created_at": {
                    "gte": start_date,
                    "lte": end_date
                }
            },
            select={
                "primary_season": True
            }
        )
        
        distribution = {}
        for analysis in analyses:
            season = analysis.primary_season
            distribution[season] = distribution.get(season, 0) + 1
        
        return distribution
    
   
    async def cleanup_old_events(self, retention_days: int) -> int:
        """Delete events older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        try:
            # Delete old events
            result = await self.prisma.analyticsevent.delete_many(
                where={
                    "event_timestamp": {
                        "lt": cutoff_date
                    }
                }
            )
            
            self.logger.info(
                f"Cleaned up {result.count} old analytics events",
                extra={
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat()
                }
            )
            
            return result.count
        except Exception as e:
            self.logger.error(
                f"Failed to cleanup old events: {e}",
                extra={"retention_days": retention_days}
            )
            raise