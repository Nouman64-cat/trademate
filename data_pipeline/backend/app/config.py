"""
app/config.py — Centralised settings loaded from .env

All tuneable constants live here. Import `settings` anywhere in the app.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AWS
    aws_s3_bucket_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "us-east-1"

    # Pinecone
    pinecone_api_key: str
    pinecone_index_name: str = "trademate-documents"

    # OpenAI
    openai_api_key: str
    embedding_model: str = "text-embedding-3-large"
    embedding_dimensions: int = 3072

    # Pipeline tuning — semantic chunking
    # breakpoint_threshold_type: "percentile" | "standard_deviation" | "interquartile"
    # "percentile" with threshold=95 → split only at the 95th-percentile similarity
    # distance, producing fewer but larger, more coherent chunks.
    semantic_breakpoint_type: str = "percentile"
    semantic_breakpoint_threshold: float = 95.0
    pinecone_upsert_batch: int = 100


settings = Settings()
