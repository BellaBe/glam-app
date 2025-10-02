# services/season-compatibility/src/services/compatibility_service.py
import time

import numpy as np

from shared.utils.exceptions import ValidationError
from shared.utils.logger import ServiceLogger

from ..repositories.compatibility_repository import CompatibilityRepository
from ..schemas.events import AIAnalysisCompletedPayload
from ..season_palettes import SCORING_WEIGHTS, SEASON_PALETTES


class CompatibilityService:
    """Business logic for season compatibility computation"""

    def __init__(
        self,
        repository: CompatibilityRepository,
        logger: ServiceLogger,
    ):
        self.repository = repository
        self.logger = logger

    def _calculate_color_distance(self, rgb1: list[int], rgb2: list[int]) -> float:
        """Calculate Euclidean distance between two RGB colors"""
        return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(rgb1, rgb2)))

    def _compute_color_compatibility(self, item_colors: list[list[int]], season_palette: dict) -> float:
        """Compute color compatibility score for a season"""
        if not item_colors:
            return 0.0

        reference_colors = season_palette["reference_colors"]
        total_score = 0.0

        # For each item color, find minimum distance to reference colors
        for item_color in item_colors:
            min_distance = min(self._calculate_color_distance(item_color, ref_color) for ref_color in reference_colors)
            # Convert distance to score (0-1, where 1 is perfect match)
            # Max possible distance is ~441 (sqrt(255^2 * 3))
            score = 1.0 - (min_distance / 441.0)
            total_score += score

        return total_score / len(item_colors)

    def _compute_axis_compatibility(self, item_colors: list[list[int]], season_palette: dict) -> float:
        """Compute compatibility based on temperature/value/chroma axes"""
        if not item_colors:
            return 0.0

        # Simple heuristic: use average color properties
        avg_rgb = np.mean(item_colors, axis=0)

        # Temperature: Red/Yellow (warm) vs Blue/Purple (cool)
        # Simple metric: ratio of red to blue
        temperature_score = avg_rgb[0] / (avg_rgb[2] + 1)  # Avoid div by zero
        normalized_temp = min(1.0, temperature_score / 255.0)

        # Value: Lightness (sum of RGB values)
        value_score = sum(avg_rgb) / (255 * 3)

        # Chroma: Saturation (distance from gray)
        gray_value = np.mean(avg_rgb)
        chroma_score = np.std(avg_rgb) / 128.0  # Normalize to 0-1

        # Calculate difference from season's ideal scores
        temp_diff = abs(normalized_temp - season_palette["temperature_score"])
        value_diff = abs(value_score - season_palette["value_score"])
        chroma_diff = abs(chroma_score - season_palette["chroma_score"])

        # Weighted combination (inverted so 1 is perfect match)
        axis_score = 1.0 - (
            SCORING_WEIGHTS["temperature"] * temp_diff
            + SCORING_WEIGHTS["value"] * value_diff
            + SCORING_WEIGHTS["chroma"] * chroma_diff
        )

        return max(0.0, axis_score)

    def compute_all_season_scores(self, rgb_colors: list[list[int]], attributes: dict) -> dict[str, float]:
        """Compute compatibility scores for all 16 seasons"""
        scores = {}

        for season_name, season_palette in SEASON_PALETTES.items():
            # Color-based scoring (60% weight)
            color_score = self._compute_color_compatibility(rgb_colors, season_palette)

            # Axis-based scoring (40% weight)
            axis_score = self._compute_axis_compatibility(rgb_colors, season_palette)

            # Combined score
            final_score = (0.6 * color_score) + (0.4 * axis_score)

            # Store as normalized field name
            field_name = season_name.lower().replace(" ", "_")
            scores[field_name] = round(final_score, 3)

        return scores

    def get_top_seasons(self, scores: dict[str, float]) -> tuple[str, str, str, float]:
        """Get top 3 seasons and max score"""
        # Convert field names back to season names
        season_scores = []
        for field_name, score in scores.items():
            season_name = field_name.replace("_", " ").title()
            # Handle special cases
            if season_name == "Light Spring":
                season_name = "Light Spring"
            elif season_name == "True Spring":
                season_name = "True Spring"
            # Continue for all seasons...
            season_scores.append((season_name, score))

        # Sort by score descending
        sorted_seasons = sorted(season_scores, key=lambda x: x[1], reverse=True)

        primary = sorted_seasons[0][0] if len(sorted_seasons) > 0 else ""
        secondary = sorted_seasons[1][0] if len(sorted_seasons) > 1 else ""
        tertiary = sorted_seasons[2][0] if len(sorted_seasons) > 2 else ""
        max_score = sorted_seasons[0][1] if len(sorted_seasons) > 0 else 0.0

        return primary, secondary, tertiary, max_score

    async def process_ai_analysis(self, payload: AIAnalysisCompletedPayload, correlation_id: str) -> dict:
        """Process AI analysis event and compute season compatibility"""
        start_time = time.time()

        # Validate RGB colors
        for color in payload.precise_colors.rgb_values:
            if len(color) != 3 or any(c < 0 or c > 255 for c in color):
                raise ValidationError("Invalid RGB color values", field="precise_colors", value=str(color))

        # Compute scores for all seasons
        scores = self.compute_all_season_scores(payload.precise_colors.rgb_values, payload.attributes.model_dump())

        # Get top seasons
        primary, secondary, tertiary, max_score = self.get_top_seasons(scores)

        # Prepare data for storage
        data = {
            "item_id": payload.item_id,
            "merchant_id": payload.merchant_id,
            "product_id": payload.product_id,
            "variant_id": payload.variant_id,
            **scores,  # All season scores
            "primary_season": primary,
            "secondary_season": secondary,
            "tertiary_season": tertiary,
            "max_score": max_score,
        }

        # Store in database
        result = await self.repository.upsert(data)

        # Calculate computation time
        computation_time_ms = (time.time() - start_time) * 1000

        self.logger.info(
            "Computed season compatibility",
            extra={
                "correlation_id": correlation_id,
                "item_id": payload.item_id,
                "primary_season": primary,
                "max_score": max_score,
                "computation_time_ms": round(computation_time_ms, 2),
            },
        )

        # Return data for event publishing
        return {"result": result, "scores": scores, "computation_time_ms": computation_time_ms}

    async def get_compatible_items(
        self, merchant_id: str, seasons: list[str], min_score: float = 0.7, limit: int = 100
    ) -> list[dict]:
        """Get items compatible with given seasons"""
        # Validate seasons
        valid_seasons = set(SEASON_PALETTES.keys())
        for season in seasons:
            if season not in valid_seasons:
                raise ValidationError(f"Invalid season name: {season}", field="seasons", value=season)

        return await self.repository.find_compatible_items(merchant_id, seasons, min_score, limit)

    async def get_item_scores(self, item_id: str) -> dict:
        """Get all season scores for an item"""
        result = await self.repository.find_by_item_id(item_id)
        if not result:
            from shared.utils.exceptions import NotFoundError

            raise NotFoundError(f"Item {item_id} not found", resource="season_compatibility", resource_id=item_id)
        return result.model_dump()
