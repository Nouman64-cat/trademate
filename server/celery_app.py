import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery(
    "trademate",
    broker=REDIS_URL,
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    include=[
        "server.tasks.training_tasks",
        "server.tasks.preference_tasks",
    ],
)

app.conf.update(
    result_expires=3600,
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

# Celery Beat Schedule
app.conf.beat_schedule = {
    "weekly-model-retraining": {
        "task": "server.tasks.training_tasks.train_all_models",
        "schedule": crontab(day_of_week=0, hour=0, minute=0),  # Sunday midnight
    },
    "daily-preference-updates": {
        "task": "server.tasks.preference_tasks.update_all_user_preferences",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
    },
}
