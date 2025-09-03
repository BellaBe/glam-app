# services/recommendation-service/src/repositories/match_repository.py
from uuid import UUID

from prisma import Prisma
from prisma.models import Match, MatchItem

from ..schemas.recommendation import RecommendationRequest


class MatchRepository:
    """Repository for match records using Prisma"""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def create_match(
        self,
        merchant_id: UUID,
        platform_name: str,
        domain: str,
        request: RecommendationRequest,
        total_matches: int,
        top_score: float | None,
    ) -> Match:
        """Create match record"""
        match = await self.prisma.match.create(
            data={
                "merchant_id": str(merchant_id),
                "platform_name": platform_name,
                "domain": domain,
                "analysis_id": request.analysis_id,
                "shopper_id": request.shopper_id,
                "anonymous_id": request.anonymous_id,
                "primary_season": request.primary_season,
                "secondary_season": request.secondary_season,
                "tertiary_season": request.tertiary_season,
                "confidence": request.confidence,
                "season_scores": request.season_scores,
                "total_matches": total_matches,
                "top_score": top_score,
            }
        )
        return match

    async def create_match_items(self, match_id: str, items: list[dict]) -> list[MatchItem]:
        """Create multiple match items"""
        match_items = []
        for item in items:
            match_item = await self.prisma.matchitem.create(
                data={
                    "match_id": match_id,
                    "item_id": item["item_id"],
                    "product_id": item["product_id"],
                    "variant_id": item["variant_id"],
                    "score": item["score"],
                    "matching_season": item["matching_season"],
                }
            )
            match_items.append(match_item)
        return match_items

    async def find_by_id(self, match_id: str) -> Match | None:
        """Find match by ID with items"""
        match = await self.prisma.match.find_unique(where={"id": match_id}, include={"match_items": True})
        return match

    async def find_by_analysis_id(self, analysis_id: str) -> Match | None:
        """Find match by analysis ID"""
        match = await self.prisma.match.find_first(where={"analysis_id": analysis_id}, include={"match_items": True})
        return match
