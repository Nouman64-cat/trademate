# Knowledge Graph API Documentation

FastAPI application for querying and managing the Memgraph knowledge graph containing Pakistan PCT and US HTS trade data.

## Overview

The Knowledge Graph API provides endpoints for:
- **Health checks** - Verify Memgraph connection
- **Statistics** - Get node and relationship counts
- **Querying** - Search and retrieve HS codes with all relationships
- **Ingestion** - Trigger Pakistan and US data ingestion scripts

## Running the API

### Start the API Server

```bash
cd knowledge_graph
python3 main.py
```

The API will be available at **http://localhost:8002**

### Interactive Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## API Endpoints

### Health & Status

#### GET `/health`
Check Memgraph database connection.

**Response:**
```json
{
  "status": "healthy",
  "message": "Memgraph connection successful",
  "database": "memgraph"
}
```

#### GET `/stats`
Get comprehensive knowledge graph statistics.

**Response:**
```json
{
  "total_nodes": 150000,
  "total_relationships": 500000,
  "pk_hs_codes": 12500,
  "us_hs_codes": 18000,
  "chapters": 98,
  "subchapters": 1250,
  "headings": 5200,
  "subheadings": 8500,
  "tariffs": 45000,
  "exemptions": 3200,
  "procedures": 1500,
  "measures": 2800,
  "cess": 850,
  "anti_dumping": 125
}
```

### Query HS Codes

#### GET `/query/hs-code/{hs_code}`
Get detailed information about a specific HS code.

**Parameters:**
- `hs_code` (path): The HS code to query
- `source` (query): "PK" or "US" (default: "PK")
- `include_embedding` (query): Include embedding vector (default: false)

**Example:**
```bash
GET /query/hs-code/010121000000?source=PK
```

**Response:**
```json
{
  "code": "010121000000",
  "description": "Pure-bred breeding horses",
  "source": "PK",
  "full_label": "01.01.21 - Pure-bred breeding horses",
  "tariffs": [
    {
      "uid": "abc123...",
      "duty_type": "CD",
      "duty_name": "Customs Duty",
      "rate": "11%",
      "valid_from": "2024-01-01",
      "valid_to": null
    }
  ],
  "exemptions": [...],
  "procedures": [...],
  "measures": [...],
  "cess": [...],
  "anti_dumping": [...]
}
```

#### GET `/query/search`
Search HS codes by description or code.

**Parameters:**
- `q` (query): Search query
- `source` (query): "PK" or "US" (default: "PK")
- `limit` (query): Max results (1-100, default: 10)

**Example:**
```bash
GET /query/search?q=horses&source=PK&limit=5
```

**Response:**
```json
[
  {
    "code": "010121000000",
    "description": "Pure-bred breeding horses",
    "source": "PK",
    "full_label": "01.01.21 - Pure-bred breeding horses"
  },
  {
    "code": "010129000000",
    "description": "Other horses",
    "source": "PK",
    "full_label": "01.01.29 - Other horses"
  }
]
```

#### GET `/query/hierarchy/{hs_code}`
Get the complete hierarchy path for an HS code.

**Parameters:**
- `hs_code` (path): The HS code
- `source` (query): "PK" or "US" (default: "PK")

**Example:**
```bash
GET /query/hierarchy/010121000000?source=PK
```

**Response:**
```json
{
  "chapter": {
    "code": "01",
    "description": "Live animals"
  },
  "subchapter": {
    "code": "01.01",
    "description": "Live horses, asses, mules and hinnies"
  },
  "heading": {
    "code": "0101",
    "description": "Live horses, asses, mules and hinnies"
  },
  "subheading": {
    "code": "0101.21",
    "description": "Pure-bred breeding animals"
  },
  "hs_code": {
    "code": "010121000000",
    "description": "Pure-bred breeding horses",
    "full_label": "01.01.21 - Pure-bred breeding horses"
  }
}
```

### Ingestion Management

#### POST `/ingest/pk`
Trigger Pakistan PCT data ingestion.

**Response:**
```json
{
  "job_id": "pk_20240423_143022",
  "source": "PK",
  "status": "pending",
  "message": "Pakistan data ingestion started"
}
```

#### POST `/ingest/us`
Trigger US HTS data ingestion.

**Response:**
```json
{
  "job_id": "us_20240423_143145",
  "source": "US",
  "status": "pending",
  "message": "US data ingestion started"
}
```

#### GET `/ingest/jobs`
List all ingestion jobs.

**Response:**
```json
[
  {
    "job_id": "pk_20240423_143022",
    "source": "PK",
    "status": "completed",
    "started_at": "2024-04-23T14:30:22",
    "completed_at": "2024-04-23T14:45:18",
    "message": "PK data ingestion completed successfully",
    "logs": [
      "INFO: Loading 12500 rows from pct codes with hierarchy.csv",
      "INFO: Generating embeddings...",
      "INFO: Writing to Neo4j...",
      "INFO: Hierarchy ingestion complete."
    ]
  }
]
```

#### GET `/ingest/job/{job_id}`
Get status of a specific ingestion job.

**Example:**
```bash
GET /ingest/job/pk_20240423_143022
```

## Integration with Admin Portal

The main TradeMate server (port 8000) proxies these endpoints under `/v1/admin/knowledge-graph/`:

- Admin routes require authentication (admin user)
- All Knowledge Graph API endpoints are accessible via the admin portal
- The admin portal provides a UI for triggering ingestion and querying HS codes

**Example from main server:**
```bash
GET http://localhost:8000/v1/admin/knowledge-graph/stats
# Proxies to → http://localhost:8002/stats
```

## Data Sources

### Pakistan PCT (PK)
- **Hierarchy**: Chapter → SubChapter → Heading → SubHeading → HSCode
- **Related Data**: Tariffs, Cess, Exemptions, Anti-dumping, Procedures, Measures
- **CSV Files**: Located in `data/PK-PCT/`

### US HTS (US)
- **Hierarchy**: HSCode nodes with embeddings
- **CSV Files**: Located in `data/US-HTS/`

## Error Handling

The API returns standard HTTP status codes:

- **200 OK** - Successful request
- **404 Not Found** - HS code or job not found
- **409 Conflict** - Ingestion already running for that source
- **500 Internal Server Error** - Database or processing error
- **503 Service Unavailable** - Memgraph connection failed

**Error Response Example:**
```json
{
  "detail": "HS Code '999999999999' not found in PK data"
}
```

## Development

### Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

Required environment variables (`.env`):
```env
MEMGRAPH_URI=bolt://localhost:7687
MEMGRAPH_USERNAME=
MEMGRAPH_PASSWORD=
OPENAI_API_KEY=your_openai_api_key
```

**Note**: The code also supports `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` as fallback environment variables for compatibility.

### Project Structure

```
knowledge_graph/
├── main.py                 # FastAPI application entry point
├── db_utils.py            # Memgraph connection & utilities
├── ingest_pk.py           # Pakistan data ingestion script
├── ingest_us.py           # US data ingestion script
├── routes/
│   ├── health.py          # Health check endpoints
│   ├── stats.py           # Statistics endpoints
│   ├── query.py           # HS code query endpoints
│   └── ingest.py          # Ingestion trigger endpoints
├── data/
│   ├── PK-PCT/           # Pakistan CSV files
│   └── US-HTS/           # US CSV files
└── README_API.md          # This file
```

## Testing

Test the API with curl:

```bash
# Health check
curl http://localhost:8002/health

# Get statistics
curl http://localhost:8002/stats

# Search HS codes
curl "http://localhost:8002/query/search?q=textile&source=PK&limit=5"

# Get specific HS code
curl "http://localhost:8002/query/hs-code/010121000000?source=PK"

# Trigger ingestion
curl -X POST http://localhost:8002/ingest/pk

# Check job status
curl http://localhost:8002/ingest/jobs
```

## Production Deployment

For production, consider:

1. **Authentication**: Add API key or JWT authentication
2. **Rate Limiting**: Prevent abuse of search endpoints
3. **Caching**: Cache frequently queried HS codes
4. **Job Storage**: Use Redis or database instead of in-memory job tracking
5. **Process Management**: Use Gunicorn or Uvicorn workers
6. **Monitoring**: Add logging, metrics, and health checks

Example production startup:
```bash
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8002
```
