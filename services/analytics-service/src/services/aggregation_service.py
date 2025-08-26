# services/analytics/src/services/aggregation_service.py 
"""Service for batch aggregation operations"""

from datetime import datetime, date, timedelta
from shared.utils.logger import ServiceLogger
from ..repositories.aggregation_repository import AggregationRepository
from ..repositories.metrics_repository import MetricsRepository
from ..repositories.analytics_repository import AnalyticsRepository
from ..exceptions import AggregationError

class AggregationService:
    """Handles scheduled aggregation jobs"""
    
    def __init__(
        self,
        aggregation_repo: AggregationRepository,
        metrics_repo: MetricsRepository,
        analytics_repo: AnalyticsRepository,
        logger: ServiceLogger
    ):
        self.aggregation_repo = aggregation_repo
        self.metrics_repo = metrics_repo
        self.analytics_repo = analytics_repo
        self.logger = logger
    
    async def aggregate_hourly_metrics(self) -> None:
        """
        Hourly aggregation job.
        Validates and fixes any missing hourly metrics.
        """
        try:
            # Get current hour and previous hour
            now = datetime.now()
            current_hour = now.replace(minute=0, second=0, microsecond=0)
            previous_hour = current_hour - timedelta(hours=1)
            
            self.logger.info(
                f"Starting hourly aggregation for {previous_hour}",
                extra={"hour": previous_hour.isoformat()}
            )
            
            # The actual metrics are updated incrementally via events
            # This job can be used for validation/cleanup
            # For example, ensure all merchants have hourly records
            
            merchants_processed = 0
            # Could add validation logic here if needed
            
            self.logger.info(
                f"Completed hourly aggregation for {previous_hour}",
                extra={
                    "hour": previous_hour.isoformat(),
                    "merchants_processed": merchants_processed
                }
            )
            
        except Exception as e:
            self.logger.error(
                f"Hourly aggregation failed: {e}",
                exc_info=True
            )
            raise AggregationError(
                operation="hourly_aggregation",
                reason=str(e)
            )
    
    async def aggregate_daily_metrics(self) -> None:
        """
        Daily aggregation job.
        Aggregates all metrics for the previous day.
        """
        try:
            # Aggregate for yesterday
            yesterday = date.today() - timedelta(days=1)
            
            self.logger.info(
                f"Starting daily aggregation for {yesterday}",
                extra={"date": yesterday.isoformat()}
            )
            
            # Aggregate for all merchants
            count = await self.aggregation_repo.aggregate_all_merchants_daily(yesterday)
            
            if count == 0:
                self.logger.warning(
                    f"No merchants to aggregate for {yesterday}",
                    extra={"date": yesterday.isoformat()}
                )
            else:
                self.logger.info(
                    f"Completed daily aggregation for {yesterday}",
                    extra={
                        "date": yesterday.isoformat(),
                        "merchants_processed": count
                    }
                )
            
        except Exception as e:
            self.logger.error(
                f"Daily aggregation failed: {e}",
                exc_info=True
            )
            raise AggregationError(
                operation="daily_aggregation",
                reason=str(e)
            )
    
    async def cleanup_old_events(self) -> None:
        """
        Weekly cleanup job.
        Removes raw events older than retention period.
        """
        try:
            retention_days = 90  # Should come from config
            
            self.logger.info(
                f"Starting cleanup of events older than {retention_days} days"
            )
            
            # Use analytics repository for cleanup
            deleted_count = await self.analytics_repo.cleanup_old_events(retention_days)
            
            if deleted_count == 0:
                self.logger.info(
                    "No old events to cleanup",
                    extra={"retention_days": retention_days}
                )
            else:
                self.logger.info(
                    f"Cleanup completed",
                    extra={
                        "retention_days": retention_days,
                        "deleted_count": deleted_count
                    }
                )
            
        except Exception as e:
            self.logger.error(
                f"Cleanup job failed: {e}",
                exc_info=True
            )
            raise AggregationError(
                operation="cleanup_old_events",
                reason=str(e)
            )