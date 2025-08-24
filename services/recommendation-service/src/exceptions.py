# services/recommendation-service/src/exceptions.py
from shared.utils.exceptions import DomainError, ValidationError


class InvalidSeasonError(ValidationError):
    """Invalid season type specified"""
    code = "INVALID_SEASON"
    
    def __init__(self, season: str):
        super().__init__(
            message=f"Invalid season type: {season}",
            field="season",
            value=season
        )


class MissingIdentifierError(ValidationError):
    """Missing shopper identifier"""
    code = "MISSING_IDENTIFIER"
    
    def __init__(self):
        super().__init__(
            message="Either shopper_id or anonymous_id is required",
            field="shopper_id",
            value=None
        )


class NoMatchesError(DomainError):
    """No matching products found"""
    code = "NO_MATCHES"
    status = 200  # Not an error, just empty result
    
    def __init__(self, seasons: list):
        super().__init__(
            message="No matching products found",
            details={"seasons": seasons}
        )