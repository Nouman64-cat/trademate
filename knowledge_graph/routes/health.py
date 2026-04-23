"""
routes/health.py — Health check and database status endpoints
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from db_utils import get_driver

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    message: str
    database: str


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Check Memgraph database connection and return health status."""
    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            result.single()
        driver.close()

        return HealthResponse(
            status="healthy",
            message="Memgraph connection successful",
            database="memgraph"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
