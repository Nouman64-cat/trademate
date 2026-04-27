"""
server/routes/data_pipeline.py — Data Pipeline Admin API

Proxies requests to the data pipeline backend and provides admin controls
for document ingestion, research pipeline, and UN Comtrade data management.
"""

import os

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from typing import Any, Optional

from routes.admin import _get_current_admin_user_id

router = APIRouter(prefix="/v1/admin/data-pipeline", tags=["Admin - Data Pipeline"])

DATA_PIPELINE_BASE_URL = os.getenv("DATA_PIPELINE_URL", "http://localhost:8001")


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]


class UploadResponse(BaseModel):
    s3_key: str
    filename: str
    size_bytes: int


class IngestResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    s3_key: str
    status: str
    message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    chunks_count: Optional[int] = None
    vectors_upserted: Optional[int] = None
    error: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Health & Status
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
async def get_pipeline_health(
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Get data pipeline health status (Pinecone, S3, OpenAI)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{DATA_PIPELINE_BASE_URL}/health", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Data pipeline backend unreachable: {exc}",
            )


# ──────────────────────────────────────────────────────────────────────────────
# Document Ingestion
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """
    Upload a document to S3 for ingestion.
    Supported formats: .pdf, .docx, .pptx, .txt
    """
    async with httpx.AsyncClient() as client:
        try:
            # Read file content
            content = await file.read()

            # Prepare multipart form data
            files = {
                "file": (file.filename, content, file.content_type or "application/octet-stream")
            }

            response = await client.post(
                f"{DATA_PIPELINE_BASE_URL}/upload",
                files=files,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=exc.response.status_code if hasattr(exc, "response") else 500,
                detail=f"Upload failed: {exc}",
            )


@router.post("/ingest", response_model=IngestResponse)
async def trigger_ingestion(
    s3_key: str,
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """
    Trigger document ingestion pipeline for an S3 key.
    Returns a job_id to poll for status.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DATA_PIPELINE_BASE_URL}/ingest",
                json={"s3_key": s3_key},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=exc.response.status_code if hasattr(exc, "response") else 500,
                detail=f"Ingestion request failed: {exc}",
            )


@router.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Poll the status of an ingestion job."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DATA_PIPELINE_BASE_URL}/ingest/{job_id}",
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job '{job_id}' not found.",
                )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Failed to get job status: {exc}",
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Data pipeline backend unreachable: {exc}",
            )


# ──────────────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────────────


class PipelineConfig(BaseModel):
    # AWS
    aws_s3_bucket_name: str
    aws_region: str

    # Pinecone
    pinecone_index_name: str

    # OpenAI
    embedding_model: str
    embedding_dimensions: int

    # Pipeline tuning
    semantic_breakpoint_type: str
    semantic_breakpoint_threshold: float
    pinecone_upsert_batch: int


@router.get("/config", response_model=PipelineConfig)
async def get_pipeline_config(
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Get current data pipeline configuration."""
    # Note: The actual config is loaded from .env in the data pipeline backend
    # For a full implementation, we'd need to expose a config endpoint there
    # or read the .env file directly (not recommended for security)

    # Return a mock config for now
    return PipelineConfig(
        aws_s3_bucket_name="trademate-documents",
        aws_region="us-east-1",
        pinecone_index_name="trademate-documents",
        embedding_model="text-embedding-3-small",
        embedding_dimensions=1536,
        semantic_breakpoint_type="percentile",
        semantic_breakpoint_threshold=95.0,
        pinecone_upsert_batch=100,
    )


@router.put("/config", response_model=PipelineConfig)
async def update_pipeline_config(
    config: PipelineConfig,
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """
    Update data pipeline configuration.

    Note: This requires modifying the .env file or database-backed config.
    For production, config should be stored in a database or parameter store.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Configuration updates require database-backed config storage. "
               "Modify .env file directly for now.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Statistics & Monitoring
# ──────────────────────────────────────────────────────────────────────────────


class PipelineStats(BaseModel):
    total_documents_ingested: int
    total_vectors_in_pinecone: int
    total_research_runs: int
    last_ingestion_time: Optional[str] = None
    last_research_time: Optional[str] = None
    s3_storage_used_bytes: Optional[int] = None


@router.get("/stats", response_model=PipelineStats)
async def get_pipeline_stats(
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Get data pipeline usage statistics."""
    # This would require querying Pinecone for vector count,
    # S3 for storage usage, and tracking ingestion/research runs
    # For now, return mock data

    return PipelineStats(
        total_documents_ingested=0,
        total_vectors_in_pinecone=0,
        total_research_runs=0,
        last_ingestion_time=None,
        last_research_time=None,
        s3_storage_used_bytes=None,
    )
