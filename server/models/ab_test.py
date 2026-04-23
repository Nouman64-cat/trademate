from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Text, Index, DateTime, Float, Integer, Boolean, ForeignKey
from sqlmodel import Field, SQLModel


class ABTestVariant(SQLModel, table=True):
    __tablename__ = "ab_test_variants"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False))
    test_name: str = Field(max_length=100)  # "route_rec_v1_vs_v2"
    variant: str = Field(max_length=20)  # "control" or "treatment"
    assigned_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )

    __table_args__ = (
        Index("ix_ab_test_user", "user_id", "test_name", unique=True),
    )


class ABTestConfig(SQLModel, table=True):
    __tablename__ = "ab_test_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    test_name: str = Field(max_length=100, unique=True)
    is_active: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, default=False))
    traffic_split: float = Field(default=0.5, sa_column=Column(Float, nullable=False, default=0.5))  # 0.5 = 50/50 split
    control_model_version: str = Field(max_length=50)
    treatment_model_version: str = Field(max_length=50)
    start_date: datetime = Field(sa_column=Column(DateTime, nullable=False))
    end_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))

    __table_args__ = (
        Index("ix_ab_test_active", "is_active", "test_name"),
    )
