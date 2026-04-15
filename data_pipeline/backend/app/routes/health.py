"""
app/routes/health.py — Service health check endpoint.

GET /health — Verifies live connectivity to S3, OpenAI, and Pinecone.
"""

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter

from app.config import settings
from app.dependencies import get_openai, get_pinecone_index, get_s3
from app.models import HealthResponse

router = APIRouter(tags=["Ops"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
def health_check():
    """
    Probes each external dependency and returns an aggregated status.
    Use this endpoint for load-balancer or uptime checks.
    """
    services: dict[str, str] = {}

    try:
        get_s3().head_bucket(Bucket=settings.aws_s3_bucket_name)
        services["s3"] = "ok"
    except (BotoCoreError, ClientError) as exc:
        services["s3"] = f"error: {exc}"

    try:
        get_openai().models.list()
        services["openai"] = "ok"
    except Exception as exc:
        services["openai"] = f"error: {exc}"

    try:
        get_pinecone_index().describe_index_stats()
        services["pinecone"] = "ok"
    except Exception as exc:
        services["pinecone"] = f"error: {exc}"

    overall = "healthy" if all(v == "ok" for v in services.values()) else "degraded"
    return HealthResponse(status=overall, services=services)
