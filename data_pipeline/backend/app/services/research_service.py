"""
app/services/research_service.py — Core logic for the research pipeline.
Handles fetching, processing (OpenAI), and storing (Pinecone/S3).
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

import boto3
from openai import OpenAI
from pinecone import Pinecone

from app.config import settings
from app.services.embedder import embed_texts
from app.services.vector_store import make_vector_id, upsert_vectors
from app.services.news_fetcher import fetch_news_by_query
from app.services.comtrade_processor import fetch_and_store_trade_data, PAKISTAN_CODE, USA_CODE

logger = logging.getLogger("trademate.research")

# ── Clients ──────────────────────────────────────────────────────────────────


def _get_openai_client():
    return OpenAI(api_key=settings.openai_api_key)


def _get_pinecone_index():
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name)


def _get_s3_client():
    client_kwargs = {
        "region_name": settings.aws_region,
    }
    is_lambda = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    if not is_lambda and settings.aws_access_key_id_manual and settings.aws_secret_access_key_manual:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id_manual
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key_manual
        logger.info("Initializing S3 client with explicit manual credentials.")
    else:
        logger.info(
            "Initializing S3 client using IAM role/environment (forced in Lambda).")

    return boto3.client("s3", **client_kwargs)

# ── Research Steps ────────────────────────────────────────────────────────────


def fetch_research_data(query: str) -> List[Dict[str, Any]]:
    """
    Fetch research data for the given query using real sources.

    Current implementation queries a set of RSS/news feeds and returns
    matching articles. Falls back to a mock item if nothing is found.
    """
    logger.info("Fetching research data for query: %s", query)

    # Try news/RSS sources first
    try:
        news_items = fetch_news_by_query(
            query,
            max_items=20,
            require_all=True,
            full_fetch_limit=10,
        )
        if news_items:
            logger.info("Fetched %d news items for query '%s'",
                        len(news_items), query)
            return news_items
    except Exception as e:
        logger.exception("News fetcher failed: %s", e)

    # Fallback: keep a small mocked item so pipeline still runs
    logger.info(
        "No live news found; using fallback mock data for query '%s'", query)
    return [
        {
            "title": f"Trade Analysis for {query}",
            "content": f"Detailed research content regarding {query} identifying trade patterns and opportunities...",
            "source": "Mock Research API",
            "url": "https://example.com/research/1",
        }
    ]


def process_research(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Uses OpenAI to summarize and extract insights from the research data.
    """
    client = _get_openai_client()
    processed_results = []

    for item in data:
        logger.info("Processing item: %s", item["title"])

        prompt = f"""
        Analyze the following trade research data and provide a concise summary, 
        key insights, and potential impact for Pakistani exporters.
        
        DATA:
        Title: {item['title']}
        Source: {item['source']}
        Content: {item['content']}
        """

        response = client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {"role": "system", "content": "You are a trade research analyst expert in Pakistani international trade."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )

        analysis = response.choices[0].message.content
        item["analysis"] = analysis
        processed_results.append(item)

    return processed_results


def store_research(results: List[Dict[str, Any]], query: str):
    """
    Stores the processed research in S3 and Pinecone.
    """
    # 1. Save to S3 (JSON)
    s3 = _get_s3_client()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    s3_key = f"research/{query.replace(' ', '_')}_{timestamp}.json"

    logger.info("Uploading research to s3://%s/%s",
                settings.aws_s3_bucket_name, s3_key)
    s3.put_object(
        Bucket=settings.aws_s3_bucket_name,
        Key=s3_key,
        Body=json.dumps(results, indent=2),
        ContentType="application/json"
    )

    # 2. Upsert to Pinecone
    logger.info("Upserting research to Pinecone index: %s",
                settings.pinecone_index_name)

    # Build full texts and batch embeddings
    full_texts: list[str] = []
    for item in results:
        full_texts.append(
            f"TITLE: {item['title']}\nANALYSIS: {item.get('analysis', '')}\nCONTENT: {item['content']}")

    logger.info("Generating embeddings for %d items...", len(full_texts))
    embeddings = embed_texts(full_texts)

    vectors = []
    for idx, (item, embedding) in enumerate(zip(results, embeddings)):
        vector_id = make_vector_id(s3_key, idx)
        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "text": full_texts[idx],
                "source": item.get("source"),
                "url": item.get("url"),
                "type": "research",
                "query": query,
                "timestamp": timestamp,
            },
        })

    # Upsert all vectors in a single call (vector_store will batch if needed)
    logger.info("Upserting %d vectors to Pinecone (batched)...", len(vectors))
    if vectors:
        upsert_vectors(vectors)

    logger.info("Research storage complete.")

# ── Orchestration ─────────────────────────────────────────────────────────────


def run_comtrade_refresh():
    """
    Refreshes the latest trade data for US-Pakistan corridors.
    Typically run as a scheduled task.
    """
    logger.info("Starting scheduled UN Comtrade data refresh for US-Pakistan...")
    # For automated hourly runs, we only fetch the most recent 2 years to stay updated
    current_year = datetime.utcnow().year
    years = [str(current_year - 1), str(current_year)]
    
    try:
        # Pakistan -> USA
        fetch_and_store_trade_data(years, PAKISTAN_CODE, USA_CODE)
        # USA -> Pakistan
        fetch_and_store_trade_data(years, USA_CODE, PAKISTAN_CODE)
        return {"status": "success", "message": f"Refreshed Comtrade data for years {years}"}
    except Exception as e:
        logger.exception("Comtrade refresh failed")
        return {"status": "error", "message": str(e)}


def run_research_pipeline(query: str, include_comtrade: bool = False):
    """
    Runs the full research pipeline.
    """
    try:
        # 1. Fetch News Research
        raw_data = fetch_research_data(query)
        processed_data = process_research(raw_data)
        store_research(processed_data, query)
        
        # 2. Optionally include Comtrade refresh if requested or for specific queries
        comtrade_result = None
        if include_comtrade or "trade stats" in query.lower() or "export volumes" in query.lower():
            comtrade_result = run_comtrade_refresh()
            
        message = f"Processed {len(processed_data)} research items."
        if comtrade_result:
            message += f" Comtrade Result: {comtrade_result['message']}"
            
        return {"status": "success", "message": message}
    except Exception as e:
        logger.exception("Research pipeline failed")
        return {"status": "error", "message": str(e)}
