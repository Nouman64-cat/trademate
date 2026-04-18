"""
app/dependencies.py — Lazy singletons for external service clients.

Each getter initialises its client exactly once and caches it for the
lifetime of the process. Swap out any getter here to change the underlying
provider without touching business logic.
"""

import os
from typing import Any

import boto3
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

from app.config import settings
from app.logger import get_logger

logger = get_logger("trademate.deps")

_s3_client: Any = None
_openai_client: OpenAI | None = None
_pinecone_index: Any = None


def get_s3():
    global _s3_client
    if _s3_client is None:
        client_kwargs = {
            "region_name": settings.aws_region,
        }
        is_lambda = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
        if not is_lambda and settings.aws_access_key_id_manual and settings.aws_secret_access_key_manual:
            client_kwargs["aws_access_key_id"] = settings.aws_access_key_id_manual
            client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key_manual
            logger.info("Initializing S3 client with explicit manual credentials.")
        else:
            logger.info("Initializing S3 client using IAM role/environment (forced in Lambda).")

        _s3_client = boto3.client("s3", **client_kwargs)
    return _s3_client


def get_openai() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def get_pinecone_index():
    """Return the Pinecone index, creating it automatically if absent."""
    global _pinecone_index
    if _pinecone_index is None:
        pc = Pinecone(api_key=settings.pinecone_api_key)
        existing = [idx.name for idx in pc.list_indexes()]
        if settings.pinecone_index_name not in existing:
            logger.info(
                "Creating Pinecone index '%s' (%d dims, cosine)…",
                settings.pinecone_index_name,
                settings.embedding_dimensions,
            )
            pc.create_index(
                name=settings.pinecone_index_name,
                dimension=settings.embedding_dimensions,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.aws_region),
            )
        _pinecone_index = pc.Index(settings.pinecone_index_name)
    return _pinecone_index
