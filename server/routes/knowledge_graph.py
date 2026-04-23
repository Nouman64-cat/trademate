"""
server/routes/knowledge_graph.py — Knowledge Graph Admin API

Proxy requests to the knowledge graph API (port 8002)
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Any, Optional

from routes.admin import _get_current_admin_user_id

router = APIRouter(prefix="/v1/admin/knowledge-graph", tags=["Admin - Knowledge Graph"])

# Knowledge graph API URL (same machine, port 8002)
KG_API_BASE_URL = "http://localhost:8002"


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str
    message: str
    database: str


class GraphStats(BaseModel):
    total_nodes: int
    total_relationships: int
    pk_hs_codes: int
    us_hs_codes: int
    chapters: int
    subchapters: int
    headings: int
    subheadings: int
    tariffs: int
    exemptions: int
    procedures: int
    measures: int
    cess: int
    anti_dumping: int


class IngestionJob(BaseModel):
    job_id: str
    source: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    message: Optional[str] = None
    logs: list[str] = []


class IngestionTriggerResponse(BaseModel):
    job_id: str
    source: str
    status: str
    message: str


class HSCodeDetail(BaseModel):
    code: str
    description: str
    source: str
    full_label: Optional[str] = None
    tariffs: list[dict] = []
    exemptions: list[dict] = []
    procedures: list[dict] = []
    measures: list[dict] = []
    cess: list[dict] = []
    anti_dumping: list[dict] = []


class SearchResult(BaseModel):
    code: str
    description: str
    source: str
    full_label: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# Health & Statistics
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
async def get_health(
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Check knowledge graph API and Memgraph connection."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{KG_API_BASE_URL}/health", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Knowledge graph API unreachable: {exc}",
            )


@router.get("/stats", response_model=GraphStats)
async def get_stats(
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Get knowledge graph statistics."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{KG_API_BASE_URL}/stats", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get stats: {exc}",
            )


# ──────────────────────────────────────────────────────────────────────────────
# Ingestion Management
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/ingest/pk", response_model=IngestionTriggerResponse)
async def trigger_pk_ingestion(
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Trigger Pakistan PCT data ingestion."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{KG_API_BASE_URL}/ingest/pk",
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 409:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Pakistan ingestion is already running",
                )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Failed to trigger ingestion: {exc}",
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Knowledge graph API unreachable: {exc}",
            )


@router.post("/ingest/us", response_model=IngestionTriggerResponse)
async def trigger_us_ingestion(
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Trigger US HTS data ingestion."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{KG_API_BASE_URL}/ingest/us",
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 409:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="US ingestion is already running",
                )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Failed to trigger ingestion: {exc}",
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Knowledge graph API unreachable: {exc}",
            )


@router.get("/jobs", response_model=list[IngestionJob])
async def get_ingestion_jobs(
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Get all ingestion jobs."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{KG_API_BASE_URL}/ingest/jobs", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get jobs: {exc}",
            )


@router.get("/job/{job_id}", response_model=IngestionJob)
async def get_job_status(
    job_id: str,
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Get status of a specific ingestion job."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{KG_API_BASE_URL}/ingest/job/{job_id}",
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Job '{job_id}' not found",
                )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Failed to get job status: {exc}",
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Knowledge graph API unreachable: {exc}",
            )


# ──────────────────────────────────────────────────────────────────────────────
# Query HS Codes
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/query/{hs_code}", response_model=HSCodeDetail)
async def query_hs_code(
    hs_code: str,
    source: str = Query("PK", description="Source: PK or US"),
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Query a specific HS code and get all related information."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{KG_API_BASE_URL}/query/hs-code/{hs_code}",
                params={"source": source},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"HS Code '{hs_code}' not found in {source} data",
                )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Failed to query HS code: {exc}",
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Knowledge graph API unreachable: {exc}",
            )


@router.get("/search", response_model=list[SearchResult])
async def search_hs_codes(
    q: str = Query(..., description="Search query"),
    source: str = Query("PK", description="Source: PK or US"),
    limit: int = Query(10, ge=1, le=100),
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Search HS codes by description."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{KG_API_BASE_URL}/query/search",
                params={"q": q, "source": source, "limit": limit},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Search failed: {exc}",
            )


@router.get("/hierarchy/{hs_code}")
async def get_hierarchy(
    hs_code: str,
    source: str = Query("PK", description="Source: PK or US"),
    admin_id: int = Depends(_get_current_admin_user_id),
):
    """Get the complete hierarchy path for an HS code."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{KG_API_BASE_URL}/query/hierarchy/{hs_code}",
                params={"source": source},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"HS Code '{hs_code}' or its hierarchy not found",
                )
            raise HTTPException(
                status_code=exc.response.status_code,
                detail=f"Failed to get hierarchy: {exc}",
            )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Knowledge graph API unreachable: {exc}",
            )
