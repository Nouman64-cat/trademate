"""
main.py — Knowledge Graph API

FastAPI application for querying and managing the Memgraph knowledge graph
containing Pakistan PCT and US HTS trade data.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import health, stats, query, ingest

app = FastAPI(
    title="TradeMate Knowledge Graph API",
    description="Query Pakistan PCT and US HTS trade data from Memgraph",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(stats.router)
app.include_router(query.router)
app.include_router(ingest.router)


@app.get("/")
def root():
    return {
        "message": "TradeMate Knowledge Graph API",
        "docs": "/docs",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
