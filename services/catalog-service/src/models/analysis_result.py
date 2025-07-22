# services/catalog-service/src/models/analysis_result.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DECIMAL, Integer, ForeignKey, Index, TIMESTAMP 
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from uuid import UUID, uuid4
from datetime import datetime
from shared.database.base import Base, TimestampedMixin

class AnalysisResult(Base, TimestampedMixin):
    """Analysis results for product items"""
    __tablename__ = "analysis_results"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Core categorization
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    subcategory: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=True)
    
    # Structured attributes (JSON as text)
    attributes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Quality metrics
    quality_score: Mapped[float] = mapped_column(DECIMAL(5,4), nullable=True, index=True)
    confidence_score: Mapped[float] = mapped_column(DECIMAL(5,4), nullable=True)
    processing_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Metadata
    analyzed_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_analysis_unique", "item_id", "model_version", unique=True),
        Index("idx_analysis_model_version", "model_version"),
    )
