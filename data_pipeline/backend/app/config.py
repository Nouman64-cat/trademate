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

    # Pipeline tuning
    chunk_size: int = 1000
    chunk_overlap: int = 200
    pinecone_upsert_batch: int = 100


settings = Settings()
