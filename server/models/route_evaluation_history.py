from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Text, Index, DateTime, Float, Integer, ForeignKey
from sqlmodel import Field, SQLModel


class RouteEvaluationHistory(SQLModel, table=True):
    __tablename__ = "route_evaluation_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    conversation_id: Optional[str] = Field(sa_column=Column(Text, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True))
    message_id: Optional[int] = Field(sa_column=Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True))

    # Request parameters
    origin_city: str = Field(max_length=100)
    destination_city: str = Field(max_length=100)
    cargo_type: str = Field(max_length=20)  # FCL20, FCL40, LCL, AIR
    cargo_value_usd: float = Field(sa_column=Column(Float, nullable=False))
    hs_code: Optional[str] = Field(default=None, max_length=10)
    cargo_volume_cbm: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))
    cargo_weight_kg: Optional[float] = Field(default=None, sa_column=Column(Float, nullable=True))
    container_count: int = Field(default=1, sa_column=Column(Integer, nullable=False, default=1))
    cost_weight: float = Field(default=0.5, sa_column=Column(Float, nullable=False, default=0.5))  # User's cost vs speed preference

    # Response summary
    routes_count: int = Field(sa_column=Column(Integer, nullable=False))
    cheapest_route_id: str = Field(max_length=100)
    fastest_route_id: str = Field(max_length=100)
    balanced_route_id: str = Field(max_length=100)
    selected_route_id: Optional[str] = Field(default=None, max_length=100)  # If user clicked

    # Full response for replay/analysis
    full_response_json: str = Field(sa_column=Column("full_response", Text, nullable=False))  # JSON

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )

    __table_args__ = (
        Index("ix_route_eval_user_created", "user_id", "created_at"),
        Index("ix_route_eval_cities", "origin_city", "destination_city"),
        Index("ix_route_eval_cargo", "cargo_type", "hs_code"),
    )
