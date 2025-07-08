# File: services/connector-service/src/models/rate_limit.py

"""Rate limit state model."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base


class RateLimitState(Base):
    """Rate limit tracking for API endpoints."""
    
    __tablename__ = "rate_limit_states"
    __table_args__ = (
        UniqueConstraint("store_id", "endpoint", name="uq_store_endpoint"),
    )
    
    # Composite key
    store_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        nullable=False
    )
    
    endpoint: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        nullable=False
    )
    
    # Rate limit tracking
    calls_made: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Calls made in current period"
    )
    
    calls_limit: Mapped[int] = mapped_column(
        Integer,
        default=40,
        nullable=False,
        comment="Maximum calls allowed"
    )
    
    # Time tracking
    reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    
    last_call_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    def __repr__(self) -> str:
        return f"<RateLimitState(store_id={self.store_id}, endpoint={self.endpoint}, {self.calls_made}/{self.calls_limit})>"
