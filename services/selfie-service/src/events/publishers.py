# services/selfie-service/src/events/publishers.py
from datetime import UTC, datetime

from shared.api.correlation import get_correlation_context
from shared.messaging.publisher import Publisher

from ..schemas.analysis import AnalysisOut
from ..schemas.events import (
    AnalysisClaimedPayload,
    AnalysisCompletedPayload,
    AnalysisFailedPayload,
    AnalysisStartedPayload,
)


class SelfieEventPublisher(Publisher):
    """Publish selfie analysis events"""

    @property
    def service_name(self) -> str:
        return "selfie-service"

    async def analysis_started(self, analysis: AnalysisOut) -> str:
        """Publish analysis started event"""
        payload = AnalysisStartedPayload(
            analysis_id=analysis.id,
            merchant_id=analysis.merchant_id,
            platform={
                "name": analysis.platform_name,
                "shop_id": analysis.platform_shop_id,
                "domain": analysis.domain,
            },
            customer_id=analysis.customer_id,
            anonymous_id=analysis.anonymous_id,
            image_dimensions={"width": analysis.image_width, "height": analysis.image_height},
            source=analysis.source,
            device_type=analysis.device_type,
            created_at=analysis.created_at,
        )

        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.selfie.analysis.started.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
        )

    async def analysis_completed(
        self,
        analysis_id: str,
        merchant_id: str,
        platform: dict,
        customer_id: Optional[str],
        anonymous_id: Optional[str],
        season_type: str,
        confidence: float,
        attributes: Optional[dict] = None,
        model_version: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
    ) -> str:
        """Publish analysis completed event"""
        payload = AnalysisCompletedPayload(
            analysis_id=analysis_id,
            merchant_id=merchant_id,
            platform=platform,
            customer_id=customer_id,
            anonymous_id=anonymous_id,
            season_type=season_type,
            confidence=confidence,
            attributes=attributes,
            model_version=model_version,
            processing_time_ms=processing_time_ms,
            completed_at=datetime.now(UTC),
        )

        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.selfie.analysis.completed.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
        )

    async def analysis_failed(
        self,
        analysis_id: str,
        merchant_id: str,
        platform: dict,
        customer_id: Optional[str],
        anonymous_id: Optional[str],
        error_code: str,
        error_message: str,
    ) -> str:
        """Publish analysis failed event"""
        payload = AnalysisFailedPayload(
            analysis_id=analysis_id,
            merchant_id=merchant_id,
            platform=platform,
            customer_id=customer_id,
            anonymous_id=anonymous_id,
            error_code=error_code,
            error_message=error_message,
            failed_at=datetime.now(UTC),
        )

        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.selfie.analysis.failed.v1", data=payload.model_dump(mode="json"), correlation_id=correlation_id
        )

    async def analyses_claimed(self, merchant_id: str, customer_id: str, anonymous_id: str, claimed_count: int) -> str:
        """Publish analyses claimed event"""
        payload = AnalysisClaimedPayload(
            merchant_id=merchant_id,
            customer_id=customer_id,
            anonymous_id=anonymous_id,
            claimed_count=claimed_count,
            claimed_at=datetime.now(UTC),
        )

        correlation_id = get_correlation_context() or "unknown"

        return await self.publish_event(
            subject="evt.selfie.analyses.claimed.v1",
            data=payload.model_dump(mode="json"),
            correlation_id=correlation_id,
        )
