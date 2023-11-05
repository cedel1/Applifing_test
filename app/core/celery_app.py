from app.core.config import settings
from celery import Celery
from celery.schedules import crontab

celery_app = Celery("worker", broker="amqp://guest@queue//",
                    result_backend = f'db+{str(settings.SQLALCHEMY_DATABASE_URI)}')

celery_app.conf.task_routes = {
    "app.worker.test_celery": "main-queue",
    "app.worker.download_product_offers": "main-queue",
    "app.worker.download_offers_for_product": "main-queue",
}
