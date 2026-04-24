"""
app/services/ingestion_pipeline.py — Orchestrates the full RAG ingestion pipeline.

Execution order:
  1. Download file from S3 to a temp path
  2. Parse + chunk the document
  3. Generate OpenAI embeddings
  4. Build vector payloads with metadata
  5. Upsert to Pinecone
  6. Clean up temp file

This module only orchestrates — it delegates to the specialised
service modules (document_parser, embedder, vector_store).
"""

import tempfile
from pathlib import Path

from botocore.exceptions import ClientError

from app.config import settings
from app.dependencies import get_s3
from app.logger import get_logger
from app.models import JobRecord, JobStatus
from app.services.document_parser import parse_and_chunk
from app.services.embedder import embed_texts
from app.services.vector_store import make_vector_id, upsert_vectors

logger = get_logger("trademate.pipeline")


def run_ingestion(job: JobRecord) -> None:
    """
    Execute the full ingestion pipeline for a single document.
    Mutates `job` in-place to reflect progress and outcome.
    Designed to run inside a FastAPI BackgroundTask.
    """
    job.status = JobStatus.RUNNING
    filename = Path(job.s3_key).name
    suffix = Path(job.s3_key).suffix.lower()
    tmp_path: str | None = None

    try:
        # ── Step 1: Download from S3 ─────────────────────────────────────
        logger.info("[%s] Downloading s3://%s/%s", job.job_id, settings.aws_s3_bucket_name, job.s3_key)
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name

        try:
            get_s3().download_file(settings.aws_s3_bucket_name, job.s3_key, tmp_path)
        except ClientError as exc:
            raise RuntimeError(f"S3 download failed: {exc}") from exc

        # ── Step 2: Parse + chunk ────────────────────────────────────────
        logger.info("[%s] Parsing and chunking (%s)…", job.job_id, suffix)
        chunks = parse_and_chunk(tmp_path)
        logger.info("[%s] Produced %d chunks", job.job_id, len(chunks))

        # ── Step 3: Embed ────────────────────────────────────────────────
        logger.info("[%s] Generating embeddings (%s)…", job.job_id, settings.embedding_model)
        texts = [c.page_content for c in chunks]
        embeddings = embed_texts(texts)

        # ── Step 4: Build vector payloads ────────────────────────────────
        vectors = [
            {
                "id": make_vector_id(job.s3_key, idx),
                "values": embedding,
                "metadata": {
                    "text":        chunk.page_content,
                    "source":      filename,
                    "s3_key":      job.s3_key,
                    "chunk_index": idx,
                    "page":        chunk.metadata.get("page", idx),
                },
            }
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]

        # ── Step 5: Upsert to Pinecone ───────────────────────────────────
        logger.info("[%s] Upserting %d vectors to Pinecone…", job.job_id, len(vectors))
        upsert_vectors(vectors)

        job.status = JobStatus.COMPLETED
        job.chunks_upserted = len(vectors)
        job.message = f"Successfully ingested {len(vectors)} chunks from '{filename}'."
        logger.info("[%s] Completed. %d chunks upserted.", job.job_id, len(vectors))

    except Exception as exc:
        job.status = JobStatus.FAILED
        job.message = str(exc)
        logger.exception("[%s] Ingestion failed: %s", job.job_id, exc)

    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
