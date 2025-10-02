# services/analytics/src/events/listeners.py
from shared.messaging.listener import Listener
from shared.utils.exceptions import ValidationError
from shared.utils.logger import ServiceLogger

from ..schemas.events import (
    CatalogSyncCompletedPayload,
    CreditsConsumedPayload,
    RecommendationMatchCompletedPayload,
    SelfieAnalysisCompletedPayload,
)
from ..services.analytics_service import AnalyticsService


class SelfieAnalysisCompletedListener(Listener):
    """Listen for selfie analysis completions"""

    @property
    def subject(self) -> str:
        return "evt.selfie.analysis.completed.v1"

    @property
    def queue_group(self) -> str:
        return "analytics-selfie-handler"

    @property
    def service_name(self) -> str:
        return "analytics-service"

    def __init__(self, js_client, analytics_service: AnalyticsService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.analytics_service = analytics_service

    async def on_message(self, data: dict) -> None:
        """Process selfie analysis completed event"""
        try:
            payload = SelfieAnalysisCompletedPayload(**data)

            # Store raw event
            await self.analytics_service.record_analytics_event(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                event_type=self.subject,
                event_data=data,
                shopper_id=payload.shopper_id,
                anonymous_id=payload.anonymous_id,
                analysis_id=payload.analysis_id,
            )

            # Record analysis metrics
            await self.analytics_service.record_shopper_analysis(payload)

            # Update hourly and daily metrics
            await self.analytics_service.update_hourly_metrics(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                timestamp=payload.analyzed_at,
                analyses_increment=1,
            )

            self.logger.info(
                f"Processed selfie analysis for merchant {payload.merchant_id}",
                extra={"analysis_id": payload.analysis_id, "season": payload.primary_season},
            )

        except ValidationError as e:
            self.logger.exception(f"Invalid selfie analysis event: {e}")
            return  # ACK invalid messages
        except Exception as e:
            self.logger.exception(f"Failed to process selfie analysis: {e}")
            raise  # NACK for retry


class RecommendationMatchCompletedListener(Listener):
    """Listen for recommendation match completions"""

    @property
    def subject(self) -> str:
        return "evt.recommendation.match.completed.v1"

    @property
    def queue_group(self) -> str:
        return "analytics-match-handler"

    @property
    def service_name(self) -> str:
        return "analytics-service"

    def __init__(self, js_client, analytics_service: AnalyticsService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.analytics_service = analytics_service

    async def on_message(self, data: dict) -> None:
        """Process recommendation match completed event"""
        try:
            payload = RecommendationMatchCompletedPayload(**data)

            # Store raw event
            await self.analytics_service.record_analytics_event(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                event_type=self.subject,
                event_data=data,
                shopper_id=payload.shopper_id,
                anonymous_id=payload.anonymous_id,
                analysis_id=payload.analysis_id,
                match_id=payload.match_id,
            )

            # Record match metrics
            await self.analytics_service.record_match_metrics(payload)

            # Update product metrics
            await self.analytics_service.update_product_metrics(payload)

            # Update hourly metrics
            await self.analytics_service.update_hourly_metrics(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                timestamp=payload.matched_at,
                matches_increment=1,
                credits_increment=payload.credits_consumed,
            )

            self.logger.info(
                f"Processed match for merchant {payload.merchant_id}",
                extra={"match_id": payload.match_id, "products_matched": payload.total_matches},
            )

        except ValidationError as e:
            self.logger.exception(f"Invalid match event: {e}")
            return
        except Exception as e:
            self.logger.exception(f"Failed to process match: {e}")
            raise


class CreditsConsumedListener(Listener):
    """Listen for credit consumption events"""

    @property
    def subject(self) -> str:
        return "evt.credits.consumed.v1"

    @property
    def queue_group(self) -> str:
        return "analytics-credits-handler"

    @property
    def service_name(self) -> str:
        return "analytics-service"

    def __init__(self, js_client, analytics_service: AnalyticsService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.analytics_service = analytics_service

    async def on_message(self, data: dict) -> None:
        """Process credits consumed event"""
        try:
            payload = CreditsConsumedPayload(**data)

            # Store raw event
            await self.analytics_service.record_analytics_event(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                event_type=self.subject,
                event_data=data,
            )

            # Update credit usage metrics
            await self.analytics_service.update_credit_usage(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                timestamp=payload.consumed_at,
                credits_consumed=payload.credits_consumed,
                remaining_balance=payload.remaining_balance,
            )

        except Exception as e:
            self.logger.exception(f"Failed to process credit consumption: {e}")
            raise


class CatalogSyncCompletedListener(Listener):
    """Listen for catalog sync completions"""

    @property
    def subject(self) -> str:
        return "evt.catalog.sync.completed.v1"

    @property
    def queue_group(self) -> str:
        return "analytics-catalog-handler"

    @property
    def service_name(self) -> str:
        return "analytics-service"

    def __init__(self, js_client, analytics_service: AnalyticsService, logger: ServiceLogger):
        super().__init__(js_client, logger)
        self.analytics_service = analytics_service

    async def on_message(self, data: dict) -> None:
        """Process catalog sync completed event"""
        try:
            payload = CatalogSyncCompletedPayload(**data)

            # Store raw event
            await self.analytics_service.record_analytics_event(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                event_type=self.subject,
                event_data=data,
            )

            # Update catalog metrics
            await self.analytics_service.update_catalog_metrics(
                merchant_id=payload.merchant_id,
                platform_name=payload.platform_name,
                platform_shop_id=payload.platform_shop_id,
                domain=payload.domain,
                total_products=payload.total_products,
                analyzed_products=payload.analyzed_products,
                synced_at=payload.synced_at,
            )

        except Exception as e:
            self.logger.exception(f"Failed to process catalog sync: {e}")
            raise
