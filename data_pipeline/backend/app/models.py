"""
app/models.py — Shared Pydantic models and enums.

Keeping schemas in one place prevents circular imports between
routes and services.
"""

from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    COMPLETED = "completed"
    FAILED    = "failed"


class JobRecord(BaseModel):
    job_id: str
    s3_key: str
    status: JobStatus = JobStatus.PENDING
    message: str = ""
    chunks_upserted: int = 0


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class IngestRequest(BaseModel):
    s3_key: str = Field(
        ...,
        description="S3 object key (path within the bucket)",
        examples=["documents/trade-policy-2024.pdf"],
    )


class IngestResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    s3_key: str
    status: JobStatus
    message: str
    chunks_upserted: int


class HealthResponse(BaseModel):
    status: str
    services: dict[str, str]
