# services/analytics/src/repositories/aggregation_repository.py
"""Repository for aggregation operations"""

from uuid import UUID
from datetime import datetime, date, timedelta
from typing import Optional, List
from prisma import Prisma
from ..exceptions import AggregationError

class AggregationRepository:
    """Repository for batch aggregation operations"""
    
    def __init__(self, prisma: Prisma):
        self.prisma = prisma
    
    async def aggregate_daily_metrics(
        self,
        merchant_id: UUID,
        target_date: date
    ) -> None:
        """Aggregate all metrics for a specific day"""
        start_time = datetime.combine(target_date, datetime.min.time())
        end_time = datetime.combine(target_date + timedelta(days=1), datetime.min.time())
        
        try:
            # Get analyses count
            analyses = await self.prisma.shopperanalysis.count(
                where={
                    "merchant_id": str(merchant_id),
                    "created_at": {
                        "gte": start_time,
                        "lt": end_time
                    }
                }
            )
            
            # Get matches count
            matches = await self.prisma.matchmetrics.count(
                where={
                    "merchant_id": str(merchant_id),
                    "created_at": {
                        "gte": start_time,
                        "lt": end_time
                    }
                }
            )
            
            # Get unique shoppers
            unique_shoppers = await self._count_unique_shoppers(
                merchant_id, start_time, end_time
            )
            
            # Get returning shoppers (had analysis before target date)
            returning_shoppers = await self._count_returning_shoppers(
                merchant_id, target_date
            )
            
            # Get average metrics
            avg_confidence = await self.prisma.shopperanalysis.aggregate(
                where={
                    "merchant_id": str(merchant_id),
                    "created_at": {
                        "gte": start_time,
                        "lt": end_time
                    }
                },
                _avg={"confidence": True}
            )
            
            avg_match_score = await self.prisma.matchmetrics.aggregate(
                where={
                    "merchant_id": str(merchant_id),
                    "created_at": {
                        "gte": start_time,
                        "lt": end_time
                    }
                },
                _avg={"avg_match_score": True}
            )
            
            avg_products_matched = await self.prisma.matchmetrics.aggregate(
                where={
                    "merchant_id": str(merchant_id),
                    "created_at": {
                        "gte": start_time,
                        "lt": end_time
                    }
                },
                _avg={"total_matches": True}
            )
            
            # Get processing time metrics
            processing_metrics = await self.prisma.shopperanalysis.aggregate(
                where={
                    "merchant_id": str(merchant_id),
                    "created_at": {
                        "gte": start_time,
                        "lt": end_time
                    }
                },
                _avg={"processing_time_ms": True}
            )
            
            # Count zero matches
            zero_matches = await self.prisma.matchmetrics.count(
                where={
                    "merchant_id": str(merchant_id),
                    "created_at": {
                        "gte": start_time,
                        "lt": end_time
                    },
                    "total_matches": 0
                }
            )
            
            # Get credits consumed
            credits_consumed = await self.prisma.creditusagemetrics.aggregate(
                where={
                    "merchant_id": str(merchant_id),
                    "date": start_time
                },
                _sum={"credits_consumed": True}
            )
            
            # Find peak hour
            peak_hour = await self._find_peak_hour(merchant_id, target_date)
            
            # Calculate derived metrics
            analysis_frequency = analyses / unique_shoppers if unique_shoppers > 0 else 0
            drop_off_rate = ((analyses - matches) / analyses * 100) if analyses > 0 else 0
            zero_match_rate = (zero_matches / matches * 100) if matches > 0 else 0
            
            # Get platform info from first event
            platform_info = await self._get_platform_info(merchant_id)
            
            # Upsert daily metrics
            await self.prisma.dailymerchantmetrics.upsert(
                where={
                    "merchant_id_date": {
                        "merchant_id": str(merchant_id),
                        "date": start_time
                    }
                },
                create={
                    "merchant_id": str(merchant_id),
                    "platform_name": platform_info["platform_name"],
                    "platform_shop_id": platform_info["platform_shop_id"],
                    "platform_domain": platform_info["platform_domain"],
                    "date": start_time,
                    "total_analyses": analyses,
                    "total_matches": matches,
                    "unique_shoppers": unique_shoppers,
                    "returning_shoppers": returning_shoppers,
                    "avg_products_matched": avg_products_matched._avg.total_matches or 0,
                    "avg_confidence_score": avg_confidence._avg.confidence or 0,
                    "avg_match_score": avg_match_score._avg.avg_match_score or 0,
                    "credits_consumed": credits_consumed._sum.credits_consumed or 0,
                    "analysis_frequency": analysis_frequency,
                    "drop_off_rate": drop_off_rate,
                    "zero_match_rate": zero_match_rate,
                    "avg_analysis_time_ms": int(processing_metrics._avg.processing_time_ms or 0),
                    "analysis_success_rate": 95.0,  # Would calculate from actual failures
                    "peak_hour": peak_hour
                },
                update={
                    "total_analyses": analyses,
                    "total_matches": matches,
                    "unique_shoppers": unique_shoppers,
                    "returning_shoppers": returning_shoppers,
                    "avg_products_matched": avg_products_matched._avg.total_matches or 0,
                    "avg_confidence_score": avg_confidence._avg.confidence or 0,
                    "avg_match_score": avg_match_score._avg.avg_match_score or 0,
                    "credits_consumed": credits_consumed._sum.credits_consumed or 0,
                    "analysis_frequency": analysis_frequency,
                    "drop_off_rate": drop_off_rate,
                    "zero_match_rate": zero_match_rate,
                    "avg_analysis_time_ms": int(processing_metrics._avg.processing_time_ms or 0),
                    "peak_hour": peak_hour
                }
            )
            
        except Exception as e:
            raise AggregationError(
                operation="daily_metrics",
                reason=str(e),
                merchant_id=str(merchant_id)
            )
    
    async def aggregate_all_merchants_daily(self, target_date: date) -> int:
        """Aggregate daily metrics for all merchants"""
        # Get distinct merchant IDs from events
        merchants = await self.prisma.analyticsevent.find_many(
            where={
                "event_timestamp": {
                    "gte": datetime.combine(target_date, datetime.min.time()),
                    "lt": datetime.combine(target_date + timedelta(days=1), datetime.min.time())
                }
            },
            distinct=["merchant_id"]
        )
        
        count = 0
        for merchant in merchants:
            try:
                await self.aggregate_daily_metrics(
                    UUID(merchant.merchant_id),
                    target_date
                )
                count += 1
            except Exception as e:
                # Log error but continue with other merchants
                print(f"Failed to aggregate for merchant {merchant.merchant_id}: {e}")
        
        return count
    
    async def _count_unique_shoppers(
        self,
        merchant_id: UUID,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Count unique shoppers in time range"""
        analyses = await self.prisma.shopperanalysis.find_many(
            where={
                "merchant_id": str(merchant_id),
                "created_at": {
                    "gte": start_time,
                    "lt": end_time
                }
            },
            select={
                "shopper_id": True,
                "anonymous_id": True
            }
        )
        
        unique_ids = set()
        for analysis in analyses:
            if analysis.shopper_id:
                unique_ids.add(f"s:{analysis.shopper_id}")
            elif analysis.anonymous_id:
                unique_ids.add(f"a:{analysis.anonymous_id}")
        
        return len(unique_ids)
    
    async def _count_returning_shoppers(
        self,
        merchant_id: UUID,
        target_date: date
    ) -> int:
        """Count shoppers who had analyses before target date"""
        # Get shoppers from target date
        target_analyses = await self.prisma.shopperanalysis.find_many(
            where={
                "merchant_id": str(merchant_id),
                "created_at": {
                    "gte": datetime.combine(target_date, datetime.min.time()),
                    "lt": datetime.combine(target_date + timedelta(days=1), datetime.min.time())
                }
            },
            select={
                "shopper_id": True,
                "anonymous_id": True
            }
        )
        
        returning_count = 0
        for analysis in target_analyses:
            # Check if this shopper had analyses before
            where_clause = {
                "merchant_id": str(merchant_id),
                "created_at": {
                    "lt": datetime.combine(target_date, datetime.min.time())
                }
            }
            
            if analysis.shopper_id:
                where_clause["shopper_id"] = analysis.shopper_id
            elif analysis.anonymous_id:
                where_clause["anonymous_id"] = analysis.anonymous_id
            else:
                continue
            
            previous = await self.prisma.shopperanalysis.count(where=where_clause)
            if previous > 0:
                returning_count += 1
        
        return returning_count
    
    async def _find_peak_hour(
        self,
        merchant_id: UUID,
        target_date: date
    ) -> Optional[int]:
        """Find hour with most activity"""
        peak = await self.prisma.hourlyusagemetrics.find_first(
            where={
                "merchant_id": str(merchant_id),
                "date": datetime.combine(target_date, datetime.min.time())
            },
            order_by={"analyses_count": "desc"}
        )
        
        return peak.hour if peak else None
    
    async def _get_platform_info(self, merchant_id: UUID) -> dict:
        """Get platform information from first event"""
        event = await self.prisma.analyticsevent.find_first(
            where={"merchant_id": str(merchant_id)},
            select={
                "platform_name": True,
                "platform_shop_id": True,
                "platform_domain": True
            }
        )
        
        if event:
            return {
                "platform_name": event.platform_name,
                "platform_shop_id": event.platform_shop_id,
                "platform_domain": event.platform_domain
            }
        
        return {
            "platform_name": "unknown",
            "platform_shop_id": "unknown",
            "platform_domain": "unknown"
        }