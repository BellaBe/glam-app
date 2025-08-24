# services/recommendation-service/src/services/recommendation_service.py
from uuid import UUID
from typing import List, Optional
from shared.utils.logger import ServiceLogger
from shared.utils.exceptions import ValidationError, NotFoundError
from ..repositories.match_repository import MatchRepository
from ..schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    MatchOut,
    MatchItemOut
)
from .season_compatibility_client import SeasonCompatibilityClient


class RecommendationService:
    """Business logic for recommendations"""
    
    def __init__(
        self,
        repository: MatchRepository,
        season_client: SeasonCompatibilityClient,
        min_score: float,
        logger: ServiceLogger
    ):
        self.repository = repository
        self.season_client = season_client
        self.min_score = min_score
        self.logger = logger
    
    async def create_recommendation(
        self,
        merchant_id: UUID,
        platform_name: str,
        platform_domain: str,
        request: RecommendationRequest,
        correlation_id: str
    ) -> RecommendationResponse:
        """Create recommendation by orchestrating with Season Compatibility Service"""
        
        # Validate season types
        valid_seasons = [
            "True Spring", "Light Spring", "Bright Spring", "Warm Spring",
            "True Summer", "Light Summer", "Cool Summer", "Soft Summer",
            "True Autumn", "Soft Autumn", "Warm Autumn", "Deep Autumn",
            "True Winter", "Bright Winter", "Cool Winter", "Deep Winter"
        ]
        
        if request.primary_season not in valid_seasons:
            raise ValidationError(
                message=f"Invalid primary season: {request.primary_season}",
                field="primary_season",
                value=request.primary_season
            )
        
        # Build seasons list
        seasons = [request.primary_season]
        if request.secondary_season:
            seasons.append(request.secondary_season)
        if request.tertiary_season:
            seasons.append(request.tertiary_season)
        
        self.logger.info(
            "Creating recommendation",
            extra={
                "correlation_id": correlation_id,
                "merchant_id": str(merchant_id),
                "analysis_id": request.analysis_id,
                "seasons": seasons
            }
        )
        
        # Call Season Compatibility Service
        compatible_items = await self.season_client.get_compatible_items(
            merchant_id=str(merchant_id),
            seasons=seasons,
            min_score=self.min_score,
            correlation_id=correlation_id
        )
        
        # Calculate top score
        top_score = max([item["score"] for item in compatible_items]) if compatible_items else None
        
        # Create match record
        match = await self.repository.create_match(
            merchant_id=merchant_id,
            platform_name=platform_name,
            platform_domain=platform_domain,
            request=request,
            total_matches=len(compatible_items),
            top_score=top_score
        )
        
        # Create match items
        if compatible_items:
            await self.repository.create_match_items(
                match_id=match.id,
                items=compatible_items
            )
        
        self.logger.info(
            "Recommendation created",
            extra={
                "correlation_id": correlation_id,
                "match_id": match.id,
                "total_matches": len(compatible_items)
            }
        )
        
        # Build response
        matches = [
            MatchItemOut(
                item_id=item["item_id"],
                product_id=item["product_id"],
                variant_id=item["variant_id"],
                score=item["score"],
                matching_season=item["matching_season"]
            )
            for item in compatible_items
        ]
        
        return RecommendationResponse(
            match_id=match.id,
            total_matches=len(compatible_items),
            matches=matches
        )
    
    async def get_match(self, match_id: str) -> MatchOut:
        """Get match by ID"""
        match = await self.repository.find_by_id(match_id)
        
        if not match:
            raise NotFoundError(
                message=f"Match {match_id} not found",
                resource="match",
                resource_id=match_id
            )
        
        return MatchOut.model_validate(match)