# services/selfie-service/src/services/selfie_service.py
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx

from shared.utils.exceptions import NotFoundError, ValidationError
from shared.utils.logger import ServiceLogger

from ..config import ServiceConfig
from ..repositories.analysis_repository import AnalysisRepository
from ..schemas.analysis import AnalysisCreate, AnalysisOut, AnalysisStatus
from ..services.image_processor import ImageProcessor


class SelfieService:
    """Business logic for selfie analysis"""

    def __init__(
        self,
        repository: AnalysisRepository,
        image_processor: ImageProcessor,
        config: ServiceConfig,
        logger: ServiceLogger,
    ):
        self.repository = repository
        self.image_processor = image_processor
        self.config = config
        self.logger = logger

    async def create_analysis(
        self,
        merchant_id: str,
        platform_name: str,
        platform_shop_id: str,
        domain: str,
        image_bytes: bytes,
        metadata: dict[str, Any],
        correlation_id: str,
    ) -> tuple[AnalysisOut, bool]:
        """
        Create or retrieve analysis.
        Returns (analysis, is_new)
        """
        # Validate identity
        customer_id = metadata.get("customer_id")
        anonymous_id = metadata.get("anonymous_id")

        if not customer_id and not anonymous_id:
            raise ValidationError(message="Either customer_id or anonymous_id is required", code="VALIDATION_ERROR")

        # Process and validate image
        image_data = await self.image_processor.validate_and_process(image_bytes)

        # Add merchant_id to hash for deduplication
        full_hash = f"{merchant_id}:{image_data['image_hash']}"

        # Check for existing analysis (deduplication)
        existing = await self.repository.find_by_hash(merchant_id, full_hash)

        if existing:
            # Check age (30-day window)
            age = datetime.now(UTC) - existing.created_at
            if age < timedelta(days=self.config.dedup_window_days):
                if existing.status != AnalysisStatus.FAILED:
                    self.logger.info(
                        "Returning existing analysis",
                        extra={"correlation_id": correlation_id, "analysis_id": existing.id, "age_days": age.days},
                    )
                    return existing, False

        # Generate new analysis ID
        analysis_id = f"ana_{uuid4().hex[:12]}"

        # Create new analysis record
        dto = AnalysisCreate(
            id=analysis_id,
            merchant_id=merchant_id,
            platform_name=platform_name,
            platform_shop_id=platform_shop_id,
            domain=domain,
            customer_id=customer_id,
            anonymous_id=anonymous_id,
            image_hash=full_hash,
            image_width=image_data["width"],
            image_height=image_data["height"],
            blur_score=image_data["blur_score"],
            exposure_score=image_data["exposure_score"],
            face_area_ratio=image_data["face_area_ratio"],
            source=metadata.get("source", "widget"),
            device_type=metadata.get("device_type"),
        )

        analysis = await self.repository.create(dto)

        self.logger.info(
            "Created new analysis",
            extra={"correlation_id": correlation_id, "analysis_id": analysis_id, "merchant_id": merchant_id},
        )

        # Store image data for background processing
        analysis._image_data = image_data["analyzer_jpeg_b64"]

        return analysis, True

    async def get_analysis(self, analysis_id: str, merchant_id: str) -> AnalysisOut:
        """Get analysis by ID"""
        analysis = await self.repository.find_by_id(analysis_id)

        if not analysis:
            raise NotFoundError(
                message=f"Analysis {analysis_id} not found", resource="analysis", resource_id=analysis_id
            )

        # Verify merchant access
        if analysis.merchant_id != merchant_id:
            raise NotFoundError(
                message=f"Analysis {analysis_id} not found", resource="analysis", resource_id=analysis_id
            )

        return analysis

    async def get_analysis_status(self, analysis_id: str, merchant_id: str) -> dict[str, Any]:
        """Get analysis status with progress"""
        analysis = await self.get_analysis(analysis_id, merchant_id)

        # Calculate progress based on status
        progress = 0
        message = "Initializing..."

        if analysis.status == AnalysisStatus.PROCESSING:
            # Estimate progress based on time elapsed
            elapsed = (datetime.now(UTC) - analysis.created_at).seconds
            if elapsed < 5:
                progress = 20
                message = "Validating image quality..."
            elif elapsed < 10:
                progress = 40
                message = "Detecting facial features..."
            elif elapsed < 15:
                progress = 60
                message = "Analyzing color attributes..."
            elif elapsed < 20:
                progress = 80
                message = "Determining season type..."
            else:
                progress = 90
                message = "Finalizing analysis..."
        elif analysis.status == AnalysisStatus.COMPLETED:
            progress = 100
            message = "Analysis complete"
        elif analysis.status == AnalysisStatus.FAILED:
            progress = 0
            message = analysis.error_message or "Analysis failed"

        return {
            "id": analysis.id,
            "status": analysis.status.value.lower(),
            "progress": progress,
            "message": message,
            "updated_at": analysis.updated_at,
        }

    async def claim_analyses(self, merchant_id: str, customer_id: str, anonymous_id: str, correlation_id: str) -> int:
        """Link anonymous analyses to customer"""
        if not customer_id or not anonymous_id:
            raise ValidationError(
                message="Both customer_id and anonymous_id required for claim", code="VALIDATION_ERROR"
            )

        count = await self.repository.claim_anonymous(
            merchant_id=merchant_id, anonymous_id=anonymous_id, customer_id=customer_id
        )

        self.logger.info(
            "Claimed anonymous analyses",
            extra={
                "correlation_id": correlation_id,
                "merchant_id": merchant_id,
                "customer_id": customer_id,
                "anonymous_id": anonymous_id,
                "count": count,
            },
        )
        if count > 0 and self.event_publisher:
            await self.event_publisher.analyses_claimed(
                merchant_id=merchant_id, customer_id=customer_id, anonymous_id=anonymous_id, claimed_count=count
            )

        return count

    async def process_ai_analysis(self, analysis_id: str, image_jpeg_b64: str, correlation_id: str):
        """Process analysis with AI analyzer (background task)"""
        try:
            analysis = await self.repository.find_by_id(analysis_id)
            if not analysis:
                self.logger.error(f"Analysis {analysis_id} not found for AI processing")
                return

            # Call AI analyzer
            async with httpx.AsyncClient(timeout=self.config.ai_analyzer_timeout) as client:
                response = await client.post(
                    f"{self.config.ai_analyzer_url}/analyze",
                    headers={
                        "Content-Type": "application/json",
                        "Idempotency-Key": analysis_id,
                        "X-Internal-API-Key": self.config.ai_analyzer_api_key,
                        "X-Correlation-ID": correlation_id,
                    },
                    json={
                        "analysis_id": analysis_id,
                        "merchant_id": analysis.merchant_id,
                        "image_jpeg_b64": image_jpeg_b64,
                        "metadata": {
                            "platform": analysis.platform_name,
                            "customer_id": analysis.customer_id,
                            "anonymous_id": analysis.anonymous_id,
                            "source": analysis.source,
                            "device_type": analysis.device_type,
                        },
                    },
                )

            if response.status_code != 200:
                raise Exception(f"AI analyzer returned {response.status_code}")

            data = response.json()
            if not data.get("success"):
                raise Exception("AI analyzer returned success=false")

            # Update analysis with results
            await self.repository.update_with_results(
                analysis_id=analysis_id,
                primary_season=data["primary_season"],
                secondary_season=data.get("secondary_season"),
                confidence=data["confidence"],
                attributes=data.get("attributes"),
                model_version=data.get("model_version"),
                processing_time=data.get("processing_ms"),
            )

            self.logger.info(
                "AI analysis completed",
                extra={
                    "correlation_id": correlation_id,
                    "analysis_id": analysis_id,
                    "season": data["primary_season"],
                    "confidence": data["confidence"],
                },
            )
            if self.event_publisher:
                await self.event_publisher.analysis_completed(
                    analysis_id=analysis_id,
                    merchant_id=analysis.merchant_id,
                    platform={
                        "name": analysis.platform_name,
                        "shop_id": analysis.platform_shop_id,
                        "domain": analysis.domain,
                    },
                    customer_id=analysis.customer_id,
                    anonymous_id=analysis.anonymous_id,
                    season_type=data["primary_season"],
                    confidence=data["confidence"],
                    attributes=data.get("attributes"),
                    model_version=data.get("model_version"),
                    processing_time_ms=data.get("processing_ms"),
                )

        except httpx.TimeoutException:
            # Let sweeper handle timeout
            self.logger.warning(f"AI timeout for analysis {analysis_id}")
        except Exception as e:
            # Mark as failed
            await self.repository.mark_failed(
                analysis_id=analysis_id, error_code="ANALYSIS_FAILED", error_message=str(e)
            )
            self.logger.error(f"AI analysis failed for {analysis_id}: {e}", extra={"correlation_id": correlation_id})
            if self.event_publisher:
                await self.event_publisher.analysis_failed(
                    analysis_id=analysis_id,
                    merchant_id=analysis.merchant_id,
                    platform={
                        "name": analysis.platform_name,
                        "shop_id": analysis.platform_shop_id,
                        "domain": analysis.domain,
                    },
                    customer_id=analysis.customer_id,
                    anonymous_id=analysis.anonymous_id,
                    error_code="ANALYSIS_FAILED",
                    error_message=str(e),
                )
