"""
app/routes/ingest.py — Document ingestion endpoints.

POST /ingest        — Submit a document for ingestion (202 Accepted)
GET  /job/{job_id}  — Poll the status of a submitted job
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.models import (
    IngestRequest,
    IngestResponse,
    JobRecord,
    JobStatus,
    JobStatusResponse,
)
from app.services.document_parser import SUPPORTED_EXTENSIONS
from app.services.ingestion_pipeline import run_ingestion

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

# In-memory job store — swap for Redis or a DB table in production
_jobs: dict[str, JobRecord] = {}


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a document for ingestion",
)
def ingest(payload: IngestRequest, background_tasks: BackgroundTasks):
    """
    Accepts an S3 key, returns a job_id immediately (202), and runs the
    full pipeline (download → parse → chunk → embed → upsert) in the background.

    Poll **GET /ingest/{job_id}** to track progress.
    """
    ext = Path(payload.s3_key).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    job_id = str(uuid.uuid4())
    job = JobRecord(job_id=job_id, s3_key=payload.s3_key)
    _jobs[job_id] = job

    background_tasks.add_task(run_ingestion, job)

    return IngestResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message="Ingestion job accepted and queued.",
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Poll ingestion job status",
)
def get_job_status(job_id: str):
    """Returns the current status and result of an ingestion job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )
    return job
