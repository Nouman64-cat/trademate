import logging
from celery_app import app

logger = logging.getLogger(__name__)

@app.task(name="server.tasks.training_tasks.train_all_models")
def train_all_models():
    """Weekly task to retrain all ML models."""
    logger.info("━━━ [CELERY] Starting weekly model retraining...")
    # TODO: Implement retraining logic
    logger.info("━━━ [CELERY] Model retraining complete (placeholder).")
