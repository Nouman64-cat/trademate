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

    # 1. Detect Source and Parse configuration
    is_scheduled = event.get("detail-type") == "Scheduled Event"
    force_refresh = bool(event.get("force_stats_refresh", False))
    query = event.get("query")

    # 1b. Smart Update Logic: only run Comtrade stats refresh at 00:00 UTC
    # unless it's a manual force_refresh or we are testing.
    should_include_comtrade = force_refresh
    if is_scheduled:
        # EventBridge events have a ISO format 'time' field
        event_time_str = event.get("time")
        if event_time_str:
            try:
                # e.g., "2026-04-19T00:00:00Z"
                from datetime import datetime
                event_time = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
                if event_time.hour == 0:
                    should_include_comtrade = True
                    logger.info("Midnight trigger detected: Including Comtrade stats refresh.")
            except Exception as e:
                logger.warning("Could not parse event time: %s", e)

    if not query:
        # Fallback for scheduled events or direct invocations without query
        query = "global trade trends and pakistan export opportunities"
        source = "Schedule" if is_scheduled else "Manual"
        logger.info("No query provided, using %s fallback: %s", source, query)

    # 2. Execute Research Pipeline
    # Hourly news research runs every time. Comtrade only runs if triggered.
    result = run_research_pipeline(query, include_comtrade=should_include_comtrade)

    # 3. Return response
    status_code = 200 if result["status"] == "success" else 500
    
    return {
        "statusCode": status_code,
        "body": json.dumps(result),
        "headers": {
            "Content-Type": "application/json"
        }
    }
