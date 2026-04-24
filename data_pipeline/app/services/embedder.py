"""
app/services/embedder.py — OpenAI embedding generation.

Isolated here so the embedding model/provider can be swapped
without touching the ingestion pipeline.
"""

from app.config import settings
from app.dependencies import get_openai


def embed_texts(texts: list[str], batch_size: int = 1000) -> list[list[float]]:
    """
    Generate embeddings for a list of text strings.

    Sends texts in batches to OpenAI to avoid the 2048-item limit.
    Returns a list of float vectors in the same order as input.
    """
    client = get_openai()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
        )
        all_embeddings.extend([item.embedding for item in response.data])

    return all_embeddings
