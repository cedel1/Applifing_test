import httpx
from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal

from .worker_tasks import (do_download_offers_for_product,
                           do_download_product_offers)


@celery_app.task(acks_late=True)
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(
    acks_late=True,
    autoretry_for=(httpx.HTTPError,),
    max_retries=3,
    retry_backoff=True,
    )
def download_offers_for_product(product_id: str) -> str:
    with SessionLocal() as db:
        return do_download_offers_for_product(db, product_id)


@celery_app.task(acks_late=True)
def download_product_offers() -> str:
    with SessionLocal() as db:
        return do_download_product_offers(db)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        settings.DOWNLOAD_NEW_OFFERS_TASK_INTERVAL_SECONDS,
        download_product_offers.s(),
        name="Download new offers",
    )
