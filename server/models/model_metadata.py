from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Text, Index, DateTime, Integer, Boolean
from sqlmodel import Field, SQLModel


class ModelMetadata(SQLModel, table=True):
    __tablename__ = "model_metadata"

    id: Optional[int] = Field(default=None, primary_key=True)
    model_name: str = Field(max_length=100, unique=True)  # "hs_code_collaborative_v2"
    model_version: str = Field(max_length=50)  # "v2"
    model_type: str = Field(max_length=50)  # "collaborative_filtering", "content_based", "hybrid"

    # Training metadata
    trained_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    training_data_start: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))  # Data range used
    training_data_end: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    training_samples_count: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True))
    hyperparameters_json: Optional[str] = Field(default=None, sa_column=Column("hyperparameters", Text, nullable=True))  # JSON

    # Evaluation metrics
    metrics_json: Optional[str] = Field(default=None, sa_column=Column("metrics", Text, nullable=True))  # JSON
    # Example: {"precision@5": 0.32, "recall@10": 0.45, "ndcg@10": 0.41, "coverage": 0.85}

    # Deployment status
    is_active: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, default=False))  # Only one active per model_type
    deployment_date: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    model_artifact_uri: Optional[str] = Field(default=None, max_length=500)  # S3 path

    # Documentation
    description: Optional[str] = Field(default=None, max_length=500)
    created_by: Optional[str] = Field(default=None, max_length=100)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, default=datetime.utcnow, nullable=False)
    )

    __table_args__ = (
        Index("ix_model_metadata_active", "is_active", "deployment_date"),
        Index("ix_model_metadata_type", "model_type", "is_active"),
    )
