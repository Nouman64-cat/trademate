from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Text, Index, DateTime, Float, Boolean, Integer, ForeignKey
from sqlmodel import Field, SQLModel


class UserPreference(SQLModel, table=True):
    __tablename__ = "user_preferences"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True))

    # Route preferences (learned from route evaluations)
    preferred_cargo_types: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON
    typical_cost_weight: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))  # 0 = fastest, 1 = cheapest
    preferred_carriers: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON
    common_routes: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON

    # Trade preferences (learned from HS code searches)
    frequent_hs_chapters: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON
    common_origin_cities: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON
    common_dest_cities: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON
    typical_cargo_value_range: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))  # JSON {"min": 1000, "max": 50000}

    # Behavioral patterns
    prefers_detailed_responses: Optional[bool] = Field(default=None, sa_column=Column(Boolean, nullable=True))
    typical_session_duration_minutes: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))
    response_quality_preference: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))  # Average rating given

    # Metadata
    last_updated: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )
    confidence_score: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))  # 0-1, based on data quantity

    __table_args__ = (
        Index("ix_user_preferences_user", "user_id"),
    )
