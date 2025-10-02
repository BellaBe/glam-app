# services/season-compatibility/src/repositories/compatibility_repository.py

from prisma import Prisma

from ..schemas.compatibility import SeasonCompatibilityOut


class CompatibilityRepository:
    """Repository using Prisma client"""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma

    async def upsert(self, data: dict) -> SeasonCompatibilityOut:
        """Upsert season compatibility scores"""
        result = await self.prisma.seasoncompatibility.upsert(
            where={"merchant_id_item_id": {"merchant_id": data["merchant_id"], "item_id": data["item_id"]}},
            create=data,
            update={**data, "updated_at": "now()"},
        )
        return SeasonCompatibilityOut.model_validate(result)

    async def find_by_item_id(self, item_id: str) -> SeasonCompatibilityOut | None:
        """Find compatibility scores by item ID"""
        result = await self.prisma.seasoncompatibility.find_unique(where={"item_id": item_id})
        return SeasonCompatibilityOut.model_validate(result) if result else None

    async def find_compatible_items(
        self, merchant_id: str, seasons: list[str], min_score: float = 0.7, limit: int = 100
    ) -> list[dict]:
        """Find items compatible with given seasons"""
        # Build dynamic WHERE clause for seasons
        season_conditions = []
        for season in seasons:
            season_field = season.lower().replace(" ", "_")
            season_conditions.append({season_field: {"gte": min_score}})

        results = await self.prisma.seasoncompatibility.find_many(
            where={"merchant_id": merchant_id, "OR": season_conditions}, order_by={"max_score": "desc"}, take=limit
        )

        # Format results with matching season
        formatted = []
        for result in results:
            # Find best matching season from requested seasons
            best_season = None
            best_score = 0
            for season in seasons:
                season_field = season.lower().replace(" ", "_")
                score = getattr(result, season_field, 0)
                if score > best_score:
                    best_score = score
                    best_season = season

            if best_season and best_score >= min_score:
                formatted.append(
                    {
                        "item_id": result.item_id,
                        "product_id": result.product_id,
                        "variant_id": result.variant_id,
                        "score": best_score,
                        "matching_season": best_season,
                    }
                )

        return formatted
