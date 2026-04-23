from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Text, Index, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class InteractionType(str, Enum):
    search_hs_code = "search_hs_code"
    view_hs_code = "view_hs_code"
    route_evaluation = "route_evaluation"
    document_retrieval = "document_retrieval"
    recommendation_click = "recommendation_click"


class UserInteraction(SQLModel, table=True):
    __tablename__ = "user_interactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    conversation_id: Optional[str] = Field(sa_column=Column(Text, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True))
    message_id: Optional[int] = Field(sa_column=Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True))

    interaction_type: str = Field(
        sa_column=Column(SAEnum(InteractionType, name="interaction_type_enum"), nullable=False)
    )

    # Entity identifiers
    hs_code: Optional[str] = Field(default=None, max_length=20)
    route_id: Optional[str] = Field(default=None, max_length=100)
    document_id: Optional[str] = Field(default=None, max_length=255)

    # Search context
    query: Optional[str] = Field(default=None, max_length=500)
    similarity_score: Optional[float] = Field(default=None)
    rank_position: Optional[int] = Field(default=None)  # Position in search results

    # Flexible metadata - using metadata_json to avoid conflict with SQLModel's metadata property
    metadata_json: Optional[str] = Field(default=None, sa_column=Column("metadata", Text, nullable=True))

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )

    __table_args__ = (
        Index("ix_interactions_user_type_created", "user_id", "interaction_type", "created_at"),
        Index("ix_interactions_conversation", "conversation_id", "created_at"),
        Index("ix_interactions_hs_code", "hs_code", "created_at"),
    )
