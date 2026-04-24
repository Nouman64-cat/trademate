# TradeMate — Data Pipeline (backend)

This directory contains the backend research/ingestion pipeline used to
fetch trade-related content, process it with OpenAI, and store embeddings
in Pinecone and JSON runs in S3.

This README explains how to run locally, tune behaviour, and deploy.

**Quick Links**

- Lambda handler: `app/services/research_handler.py`
- Research pipeline: `app/services/research_service.py`
- News fetcher: `app/services/news_fetcher.py`
- Ingestion pipeline (file -> embeddings): `app/services/ingestion_pipeline.py`
- Pinecone verifier script: `verify_pinecone.py`
- Deployment config: `serverless.yml`

## Prerequisites

- Python 3.11+ (project uses a `.venv` in this folder)
- AWS credentials/profile with permissions to deploy and run Lambda
- `OPENAI_API_KEY`, `PINECONE_API_KEY`, `AWS_S3_BUCKET_NAME` set in `.env`

## Install

From `data_pipeline/backend`:

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

## Environment

Copy `.env.example` to `.env` and fill the keys. Required keys used by the
pipeline:

- `OPENAI_API_KEY` — OpenAI API key for chat completions + embeddings
- `PINECONE_API_KEY` — Pinecone API key
- `PINECONE_INDEX_NAME` — (optional) defaults to `trademate-documents`
- `AWS_S3_BUCKET_NAME` — S3 bucket where research JSON is stored
- `AWS_ACCESS_KEY_ID_MANUAL` / `AWS_SECRET_ACCESS_KEY_MANUAL` — optional local IAM keys
- `AWS_REGION` — e.g. `us-east-1`

The scripts read `.env` using `python-dotenv` when run locally.

## Run locally (quick)

Use the project venv so imports and packages match the Lambda runtime:

```bash
cd data_pipeline/backend
.venv/bin/python3 - <<'PY'
import json
from dotenv import load_dotenv
load_dotenv('.env')
from app.services.research_handler import lambda_handler
print(json.dumps(lambda_handler({'query':'trade between US and Pakistan'}, None), indent=2))
PY
```

This will run the full research pipeline (fetch → analyze → embed → upsert).

## What the pipeline does

- Fetches articles from a small curated RSS list (`app/services/news_fetcher.py`).
- Filters matches by query keywords (default: require all keywords — AND).
- Extracts article text (limited to `full_fetch_limit` items to reduce outbound HTTP).
- Sends each item to OpenAI for analysis and generates embeddings.
- Stores the run JSON under `research/<query>_<timestamp>.json` in S3.
- Upserts embeddings into Pinecone index (`PINECONE_INDEX_NAME`).

## Tuning

- `max_items` — maximum articles fetched per run (default 20).
- `require_all` — if true, requires all query keywords to match (AND). Set to false for OR matching.
- `full_fetch_limit` — how many matched items will have their article pages fetched and parsed (default 10).
- `pinecone_upsert_batch` — configured in `app/config.py`, controls upsert chunking.

Change these values in `app/services/news_fetcher.py` or where `fetch_news_by_query` is called
in `app/services/research_service.py`.

## Batching & Cost optimisations

- Embeddings are batched (single `embed_texts` call) to reduce API calls.
- Vector upserts are batched into one `upsert_vectors` call (the `vector_store` will chunk server-side).
- Chat completions are currently executed per item. To further reduce calls, you can batch items into a single prompt and parse responses — request if you want this implemented.

## Test Pinecone & S3

- Verify Pinecone connectivity and count vectors:

```bash
cd data_pipeline/backend
python verify_pinecone.py
```

This script also prints the last 3 `research/` JSON objects from S3 (requires S3 List/Get permissions).

## Data Sources

### 1. News & Trends (RSS/Web)
- Fetches articles from a curated RSS list (`app/services/news_fetcher.py`).
- Filters matches by query keywords and extracts full article text using OpenAI for summarization.

### 2. Trade Statistics (UN Comtrade)
- Fetches official bilateral trade data between the US and Pakistan using the UN Comtrade Public API.
- Converts numeric trade records into descriptive text (e.g., *"In 2023, Pakistan exported Cotton to the USA worth $520.45 million"*) for RAG-based analysis.

## Automated Updates (Smart Hybrid Schedule)

The pipeline is designed to be cost and performance-efficient by using a hybrid schedule:

- **Hourly**: Fetches latest news, trends, and market sentiment.
- **Daily (00:00 UTC)**: Triggers a "Trade Stats Refresh" for the UN Comtrade data. Since official stats change less frequently, this saves on API and embedding costs.
- **Manual Force**: You can force a stats update at any time by passing `"force_stats_refresh": true` in the Lambda event payload.

## Manual Utility Commands

Use these commands for maintenance and testing (using the project `.venv`):

- **Fetch US-Pakistan Trade Data (5-year history)**:
  ```bash
  ./.venv/bin/python -m app.services.comtrade_processor
  ```

- **Verify Search Results**:
  ```bash
  # Test searching the index for trade-specific data
  ./.venv/bin/python -c "from app.services.research_handler import lambda_handler; print(lambda_handler({'query':'US Pakistan textile trade stats'}, None))"
  ```

- **Clear Pinecone Index**:
  ```bash
  # Delete all vectors from the index (requires confirmation)
  ./.venv/bin/python clear_pinecone.py
  ```

- **Verify Index Stats**:
  ```bash
  ./.venv/bin/python verify_pinecone.py
  ```

## Deployment

This project deploys as a Lambda using Serverless Framework with an ECR image.
Deploy (from `data_pipeline/backend`):

```bash
npx serverless deploy --stage dev --aws-profile zygotrix --region us-east-1
```

> [!IMPORTANT]
> Because this project uses Docker images for Lambda, `serverless invoke local` is not supported. Use the manual Python commands listed above for local testing.
