from celery import Celery
from app.core.config import settings

# Initialize the Celery application
# 'broker' is where tasks wait in line (Redis)
# 'backend' is where Celery stores the final result of the task (also Redis for now)

celery_app = Celery("insight_worker", 
                    broker=settings.REDIS_URL, 
                    backend=settings.REDIS_URL,
                    include=['app.worker.task']
                    )

# Optional: Configuration for production readiness
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)