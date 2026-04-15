"""
app/services/embedder.py — OpenAI embedding generation.

Isolated here so the embedding model/provider can be swapped
without touching the ingestion pipeline.
"""

from app.config import settings
from app.dependencies import get_openai


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text strings.

    Sends all texts in a single API call (OpenAI handles batching
    internally up to its token limit).
    Returns a list of float vectors in the same order as input.
    """
    client = get_openai()
    response = client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [item.embedding for item in response.data]
