"""
routes/ingest.py — Trigger and monitor data ingestion
"""

import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/ingest", tags=["Ingestion"])

# In-memory job tracking
_jobs: dict[str, dict] = {}

# Scripts directory
SCRIPTS_DIR = Path(__file__).parent.parent


class IngestionJob(BaseModel):
    job_id: str
    source: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    message: Optional[str] = None
    logs: list[str] = []


class TriggerResponse(BaseModel):
    job_id: str
    source: str
    status: str
    message: str


async def run_ingestion(job_id: str, source: str):
    """Run ingestion script in background."""
    script_name = f"ingest_{source.lower()}.py"
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["message"] = f"Ingestion script not found: {script_name}"
        _jobs[job_id]["completed_at"] = datetime.now().isoformat()
        return

    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["logs"] = []

    try:
        # Run the ingestion script
        process = await asyncio.create_subprocess_exec(
            "python3",
            str(script_path),
            cwd=str(SCRIPTS_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        # Capture output
        logs = []
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            log_line = line.decode().strip()
            logs.append(log_line)
            _jobs[job_id]["logs"] = logs[-100:]  # Keep last 100 lines

        await process.wait()

        if process.returncode == 0:
            _jobs[job_id]["status"] = "completed"
            _jobs[job_id]["message"] = f"{source} data ingestion completed successfully"
        else:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["message"] = f"Ingestion failed with return code {process.returncode}"

    except Exception as e:
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["message"] = f"Error running ingestion: {str(e)}"
        _jobs[job_id]["logs"].append(f"ERROR: {str(e)}")

    finally:
        _jobs[job_id]["completed_at"] = datetime.now().isoformat()


@router.post("/pk", response_model=TriggerResponse)
async def trigger_pk_ingestion(background_tasks: BackgroundTasks):
    """
    Trigger Pakistan PCT data ingestion.

    Runs the ingest_pk.py script which processes:
    - HS Code hierarchy (Chapter → SubChapter → Heading → SubHeading → HSCode)
    - Tariffs (multiple duty types)
    - Cess collection
    - Exemptions/Concessions
    - Anti-dumping duties
    - Procedures
    - Measures

    The script uses checkpointing to skip already-ingested data.
    """
    # Check if another PK ingestion is running
    for job in _jobs.values():
        if job["source"] == "PK" and job["status"] in ("pending", "running"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Pakistan ingestion is already running",
            )

    job_id = f"pk_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    _jobs[job_id] = {
        "job_id": job_id,
        "source": "PK",
        "status": "pending",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "message": "Ingestion queued",
        "logs": [],
    }

    background_tasks.add_task(run_ingestion, job_id, "PK")

    return TriggerResponse(
        job_id=job_id,
        source="PK",
        status="pending",
        message="Pakistan data ingestion started",
    )


@router.post("/us", response_model=TriggerResponse)
async def trigger_us_ingestion(background_tasks: BackgroundTasks):
    """
    Trigger US HTS data ingestion.

    Runs the ingest_us.py script which processes:
    - US HTS hierarchy
    - HS Code nodes with embeddings

    The script uses checkpointing to skip already-ingested data.
    """
    # Check if another US ingestion is running
    for job in _jobs.values():
        if job["source"] == "US" and job["status"] in ("pending", "running"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="US ingestion is already running",
            )

    job_id = f"us_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    _jobs[job_id] = {
        "job_id": job_id,
        "source": "US",
        "status": "pending",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "message": "Ingestion queued",
        "logs": [],
    }

    background_tasks.add_task(run_ingestion, job_id, "US")

    return TriggerResponse(
        job_id=job_id,
        source="US",
        status="pending",
        message="US data ingestion started",
    )


@router.get("/jobs", response_model=list[IngestionJob])
async def get_jobs():
    """Get all ingestion jobs."""
    jobs = []
    for job_data in _jobs.values():
        jobs.append(IngestionJob(**job_data))
    return sorted(jobs, key=lambda x: x.started_at, reverse=True)


@router.get("/job/{job_id}", response_model=IngestionJob)
async def get_job(job_id: str):
    """Get status of a specific ingestion job."""
    if job_id not in _jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found",
        )

    return IngestionJob(**_jobs[job_id])
