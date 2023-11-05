import httpx
from fastapi import HTTPException

from app import crud
from app.api.offer_api_auth import auth_token
from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal


@celery_app.task(acks_late=True)
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(
    acks_late=True,
    autoretry_for=(httpx.HTTPError,),
    max_retries=3,
    retry_backoff=True,
    )
def download_offers_for_product(product_id: str) -> None:
    try:
        with httpx.Client() as client:
            db = SessionLocal()
            token = auth_token()
            headers = {'Authorization': f"Bearer: {token}"}
            offers_get_response = client.post(
                f"{settings.OFFER_SERVICE_BASE_URL}/api/v1/products/{product_id}/offers",
                headers=headers,
            )
            offers_get_response.raise_for_status()
            offers = offers_get_response.json()
            for offer in offers:
                crud.offer.create_or_update(db=db, obj_in=offer)
    except (httpx.HTTPError, KeyError, ValueError, HTTPException):
        raise Exception(f"Task download_offers_for_product({product_id}) failed")


def _get_number_of_batches(number_of_products):
    number_of_batches = 1
    if number_of_products > settings.API_MAX_RECORDS_LIMIT:
        number_of_batches = (
            number_of_products // settings.API_MAX_RECORDS_LIMIT
            + (0 if ((number_of_products % settings.API_MAX_RECORDS_LIMIT) > 0) else 1))
    return number_of_batches


@celery_app.task(acks_late=True)
def download_product_offers() -> None:
    db = SessionLocal()
    number_of_products = crud.product.get_number_of_products(db=db)
    number_of_batches = _get_number_of_batches(number_of_products)

    for i in range(number_of_batches):
        product_only_ids_result = crud.product.get_multi_id(db=db, skip=i * settings.API_MAX_RECORDS_LIMIT,
                                                       limit=settings.API_MAX_RECORDS_LIMIT)
        for product in product_only_ids_result:
            celery_app.send_task("app.worker.download_offers_for_product", args=[str(product.id)])


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        settings.DOWNLOAD_NEW_OFFERS_TASK_INTERVAL_SECONDS,
        download_product_offers.s(),
        name="Download new offers",
    )
