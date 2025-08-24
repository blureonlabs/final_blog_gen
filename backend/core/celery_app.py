from celery import Celery
from core.config import settings
import os

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create Celery instance
celery_app = Celery(
    "bulk_blog_generator",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "tasks.content_generation",
        "tasks.seo_optimization", 
        "tasks.blog_formatting",
        "tasks.image_generation",
        "tasks.wordpress_publishing"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing
celery_app.conf.task_routes = {
    "tasks.content_generation.*": {"queue": "content_generation"},
    "tasks.seo_optimization.*": {"queue": "seo_optimization"},
    "tasks.blog_formatting.*": {"queue": "blog_formatting"},
    "tasks.image_generation.*": {"queue": "image_generation"},
    "tasks.wordpress_publishing.*": {"queue": "wordpress_publishing"},
}

if __name__ == "__main__":
    celery_app.start()
