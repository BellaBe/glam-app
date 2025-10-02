from datetime import datetime

from prisma import Prisma

from ..schemas.analysis import AnalysisCreate, AnalysisOut, AnalysisStatus


class AnalysisRepository:
    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def create(self, dto: AnalysisCreate) -> AnalysisOut:
        analysis = await self.prisma.analysis.create(data=dto.model_dump())
        return AnalysisOut.model_validate(analysis)

    async def find_by_id(self, analysis_id: str) -> AnalysisOut | None:
        analysis = await self.prisma.analysis.find_unique(where={"id": analysis_id})
        return AnalysisOut.model_validate(analysis) if analysis else None

    async def find_by_hash(self, merchant_id: str, image_hash: str) -> AnalysisOut | None:
        analysis = await self.prisma.analysis.find_unique(
            where={"merchant_id_image_hash": {"merchant_id": merchant_id, "image_hash": image_hash}}
        )
        return AnalysisOut.model_validate(analysis) if analysis else None

    async def update_with_results(
        self,
        analysis_id: str,
        primary_season: str,
        secondary_season: str | None,
        confidence: float,
        attributes: dict | None,
        model_version: str | None,
        processing_time: int | None,
    ):
        await self.prisma.analysis.update(
            where={"id": analysis_id},
            data={
                "status": AnalysisStatus.COMPLETED.value,
                "primary_season": primary_season,
                "secondary_season": secondary_season,
                "confidence": confidence,
                "attributes": attributes,
                "model_version": model_version,
                "processing_time": processing_time,
                "completed_at": datetime.now(timezone.utc),
                "progress": 100,
            },
        )

    async def mark_failed(self, analysis_id: str, error_code: str, error_message: str):
        await self.prisma.analysis.update(
            where={"id": analysis_id},
            data={
                "status": AnalysisStatus.FAILED.value,
                "error_code": error_code,
                "error_message": error_message,
                "progress": 0,
            },
        )

    async def claim_anonymous(self, merchant_id: str, anonymous_id: str, customer_id: str) -> int:
        result = await self.prisma.analysis.update_many(
            where={"merchant_id": merchant_id, "anonymous_id": anonymous_id, "customer_id": None},
            data={"customer_id": customer_id, "claimed_at": datetime.now(timezone.utc)},
        )
        return result.count

    async def mark_stale_as_failed(self, cutoff: datetime) -> int:
        result = await self.prisma.analysis.update_many(
            where={"status": AnalysisStatus.PROCESSING.value, "created_at": {"lt": cutoff}},
            data={
                "status": AnalysisStatus.FAILED.value,
                "error_code": "PROCESSING_TIMEOUT",
                "error_message": "Analysis timed out",
            },
        )
        return result.count
