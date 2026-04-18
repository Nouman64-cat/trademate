"""
app/services/research_handler.py — Entry point for AWS Lambda research pipeline.
Handles JSON payloads (e.g., from API Gateway or scheduled events).
"""

import json
import logging
from app.services.research_service import run_research_pipeline

# ── Logging ──────────────────────────────────────────────────────────────────
from app.logger import configure_logging, get_logger

configure_logging()
logger = get_logger("trademate.lambda")

def lambda_handler(event: dict, context: object) -> dict:
    """
    Main Lambda entry point.
    
    Expected input format:
    {
        "query": "textile exports to USA",
        "options": { ... }
    }
    """
    logger.info("Lambda event received: %s", json.dumps(event))

    # 1. Detect Source and Parse query
    is_scheduled = event.get("detail-type") == "Scheduled Event"
    query = event.get("query")

    if not query:
        # Fallback for scheduled events or direct invocations without query
        query = "global trade trends and pakistan export opportunities"
        source = "Schedule" if is_scheduled else "Manual"
        logger.info("No query provided, using %s fallback: %s", source, query)

    # 2. Execute Research Pipeline
    result = run_research_pipeline(query)

    # 3. Return response
    status_code = 200 if result["status"] == "success" else 500
    
    return {
        "statusCode": status_code,
        "body": json.dumps(result),
        "headers": {
            "Content-Type": "application/json"
        }
    }
