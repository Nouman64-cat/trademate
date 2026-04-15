"""
main.py — Application entry point.

Creates the FastAPI app, registers routers, and configures middleware.
All business logic lives in app/.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.logger import configure_logging
from app.routes import health, ingest, upload

configure_logging()

app = FastAPI(
    title="TradeMate Document Ingestion API",
    description="RAG ingestion pipeline: S3 → parse → chunk → embed → Pinecone",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(ingest.router)
