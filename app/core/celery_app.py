from app.core.config import settings
from celery import Celery
from celery.schedules import crontab

celery_app = Celery("worker", broker=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_SERVER}:6379/0",
                    result_backend=f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_SERVER}:6379/0")

celery_app.conf.task_routes = {
    "app.worker.test_celery": "main-queue",
    "app.worker.download_product_offers": "main-queue",
    "app.worker.download_offers_for_product": "main-queue",
}
