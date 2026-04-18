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

## Deployment

This project deploys as a Lambda using Serverless Framework with an ECR image.
Deploy (from `data_pipeline/backend`):

```bash
npx serverless deploy --stage dev --aws-profile zygotrix --region us-east-1
```

Notes:

- The scheduled trigger is defined in `serverless.yml`. To change the cron, edit
  the `events` -> `schedule` expression under the `researcher` function. Example hourly cron:
  `cron(0 0/1 * * ? *)`.
- Ensure the Lambda's environment variables include the same keys as your local `.env`.

## Logs & Monitoring

- Tail logs with the AWS CLI (v2 recommended):

```bash
aws --profile zygotrix --region us-east-1 logs tail /aws/lambda/trademate-research-pipeline-dev-researcher-img --follow --since 1h
```

Or use `filter-log-events` on AWS CLI v1.

## IAM & Permissions

- The function requires S3 `PutObject`/`GetObject` and Pinecone/OpenAI network access.
- For local S3 access use `AWS_ACCESS_KEY_ID_MANUAL` and `AWS_SECRET_ACCESS_KEY_MANUAL` in `.env` or run with a profile.

## Troubleshooting

- `AccessDenied` when listing S3: ensure the IAM user/role has `s3:ListBucket` on the bucket and `s3:GetObject` on the `research/` prefix.
- If no news results are returned: try a broader query, set `require_all=False`, or increase `max_items`.
- High runtime/billed duration: reduce `max_items`, lower `full_fetch_limit`, or increase the Lambda `timeout`/memory depending on needs.

## Contributing

- Keep changes minimal and configuration-driven. When adding new fetchers (UN Comtrade, SAM.gov), add a dedicated module under `app/services/` and call it from `fetch_research_data` in `research_service.py`.

If you want, I can add a UN Comtrade fetcher next (structured trade flows) — tell me and I'll implement it.
