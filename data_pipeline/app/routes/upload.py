"""
app/routes/upload.py — File upload endpoint.

POST /upload  — Accepts a multipart file, saves it to S3, and returns
                the S3 key so the caller can immediately pass it to POST /ingest.
"""

from pathlib import Path

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.config import settings
from app.dependencies import get_s3
from app.logger import get_logger
from app.services.document_parser import SUPPORTED_EXTENSIONS

router = APIRouter(tags=["Upload"])

logger = get_logger("trademate.upload")

UPLOAD_PREFIX = "uploads"


class UploadResponse(BaseModel):
    s3_key: str
    filename: str
    size_bytes: int


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document to S3",
)
async def upload_file(file: UploadFile):
    """
    Upload a document from the client directly to S3.
    Returns the S3 key, which can then be passed to POST /ingest.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    s3_key = f"{UPLOAD_PREFIX}/{file.filename}"
    contents = await file.read()

    try:
        get_s3().put_object(
            Bucket=settings.aws_s3_bucket_name,
            Key=s3_key,
            Body=contents,
            ContentType=file.content_type or "application/octet-stream",
        )
    except ClientError as exc:
        logger.exception("S3 upload failed for key '%s': %s", s3_key, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload file to S3: {exc}",
        ) from exc

    logger.info("Uploaded '%s' → s3://%s/%s (%d bytes)",
                file.filename, settings.aws_s3_bucket_name, s3_key, len(contents))

    return UploadResponse(s3_key=s3_key, filename=file.filename or "", size_bytes=len(contents))
