"""
app/services/vector_store.py — Pinecone upsert logic.

All Pinecone-specific code is contained here. To switch vector
databases, only this file needs to change.
"""

import hashlib

from app.config import settings
from app.dependencies import get_pinecone_index
from app.logger import get_logger

logger = get_logger("trademate.vector_store")


def make_vector_id(s3_key: str, chunk_index: int) -> str:
    """
    Deterministic, collision-safe vector ID.
    Re-ingesting the same file will overwrite, never duplicate.
    """
    raw = f"{s3_key}::chunk::{chunk_index}"
    return hashlib.sha256(raw.encode()).hexdigest()


def upsert_vectors(vectors: list[dict]) -> None:
    """
    Upsert a list of {id, values, metadata} dicts to Pinecone
    in batches of settings.pinecone_upsert_batch.
    """
    index = get_pinecone_index()
    total = len(vectors)
    batch_size = settings.pinecone_upsert_batch

    for start in range(0, total, batch_size):
        batch = vectors[start: start + batch_size]
        index.upsert(vectors=batch)
        logger.debug("Upserted vectors %d–%d of %d", start, start + len(batch), total)
