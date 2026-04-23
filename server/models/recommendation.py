from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, DateTime, Boolean
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class RecommendationType(str, Enum):
    route = "route"
    hs_code = "hs_code"
    document = "document"
    tariff_optimization = "tariff_optimization"


class RecommendationResult(SQLModel, table=True):
    __tablename__ = "recommendation_results"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    conversation_id: Optional[str] = Field(sa_column=Column(Text, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True))
    message_id: Optional[int] = Field(sa_column=Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True))

    # Recommendation metadata
    recommendation_type: str = Field(
        sa_column=Column(SAEnum(RecommendationType, name="recommendation_type_enum"), nullable=False)
    )
    model_version: str = Field(max_length=50)  # "content_based_v1", "collaborative_v2", etc.
    algorithm_used: str = Field(max_length=100)  # "neo4j_vector", "als", "hybrid"

    # What was recommended
    recommended_items: str = Field(sa_column=Column(Text, nullable=False))  # JSON array
    context_json: Optional[str] = Field(default=None, sa_column=Column("context", Text, nullable=True))  # JSON (trigger context)

    # User feedback (explicit)
    selected_item_id: Optional[str] = Field(default=None, max_length=100)
    selection_rank: Optional[int] = Field(default=None)  # Which position they selected
    time_to_selection_seconds: Optional[float] = Field(default=None)
    was_helpful: Optional[bool] = Field(default=None, sa_column=Column(Boolean, nullable=True))

    # User feedback (implicit)
    implicit_feedback_score: Optional[float] = Field(default=None)  # Dwell time, etc.

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    )

    __table_args__ = (
        Index("ix_recommendations_user_type", "user_id", "recommendation_type", "created_at"),
        Index("ix_recommendations_model", "model_version", "created_at"),
    )
