"""
app/services/lambda_handler.py — Lambda entry point for S3-triggered ingestion.

Triggered automatically when a file lands under the uploads/ prefix in S3.
Runs the full ingestion pipeline (parse → chunk → embed → Pinecone) and
writes a status record back to pipeline-status/{job_id}.json so the FastAPI
service can report progress without holding any in-memory state.

Expected S3 key format: uploads/{job_id}/{filename}

Failure handling:
  Any unhandled exception is re-raised after attempting to write a FAILED
  status to S3. Re-raising causes Lambda to register the invocation as a
  failure, triggering up to 2 automatic retries. After all retries are
  exhausted the event is forwarded to the DLQ via EventInvokeConfig.
"""

import json
import urllib.parse
from datetime import datetime, timezone

from app.config import settings
from app.dependencies import get_s3
from app.logger import configure_logging, get_logger
from app.models import JobRecord, JobStatus
from app.services.ingestion_pipeline import run_ingestion

configure_logging()
logger = get_logger("trademate.lambda.ingestion")

STATUS_PREFIX = "pipeline-status"


def _write_status(job: JobRecord) -> None:
    payload = {
        "job_id": job.job_id,
        "s3_key": job.s3_key,
        "status": job.status,
        "message": job.message,
        "chunks_upserted": job.chunks_upserted,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    get_s3().put_object(
        Bucket=settings.aws_s3_bucket_name,
        Key=f"{STATUS_PREFIX}/{job.job_id}.json",
        Body=json.dumps(payload),
        ContentType="application/json",
    )
    logger.info("[%s] Status written: %s", job.job_id, job.status)


def handler(event: dict, context: object) -> dict:
    """
    Lambda handler. Receives an S3 ObjectCreated event and runs ingestion.

    Any exception escaping this function causes Lambda to mark the invocation
    as failed → automatic retries → DLQ after retries are exhausted.
    """
    job: JobRecord | None = None

    try:
        record = event["Records"][0]["s3"]
        bucket = record["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["object"]["key"])

        logger.info("S3 trigger — bucket=%s key=%s", bucket, key)

        # Key format: uploads/{job_id}/{filename}
        parts = key.split("/")
        if len(parts) < 3:
            # Raise — do NOT return a 400. Returning any dict counts as a
            # Lambda success and would bypass retries and the DLQ entirely.
            raise ValueError(
                f"Unexpected S3 key format (expected uploads/job_id/filename): {key}"
            )

        job_id = parts[1]
        job = JobRecord(job_id=job_id, s3_key=key, status=JobStatus.RUNNING)

        _write_status(job)
        run_ingestion(job)
        _write_status(job)

        status_code = 200 if job.status == JobStatus.COMPLETED else 500
        return {
            "statusCode": status_code,
            "body": json.dumps({"status": job.status, "message": job.message}),
        }

    except Exception as exc:
        logger.exception("Handler failed — will retry then route to DLQ: %s", exc)

        # Best-effort: write FAILED status so the admin portal shows an error
        # rather than staying stuck on "running". If this write also fails,
        # swallow it and let the re-raise below trigger the DLQ path.
        if job is not None:
            try:
                job.status = JobStatus.FAILED
                job.message = f"Ingestion failed: {exc}"
                _write_status(job)
            except Exception:
                logger.warning("[%s] Could not write FAILED status to S3", job.job_id)

        raise  # Re-raise → Lambda registers failure → retries → DLQ
