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
def download_offers_for_product(product_id: str) -> bool:
    try:
        with httpx.Client() as client:
            with SessionLocal() as db:
                token = auth_token()
                headers = {"Bearer": token}
                offers_get_response = client.get(
                    f"{settings.OFFER_SERVICE_BASE_URL}api/v1/products/{product_id}/offers",
                    headers=headers,
                )
                offers_get_response.raise_for_status()
                offers = offers_get_response.json()
                new_offer_ids = set()
                for offer in offers:
                    crud.offer.create_or_update(db=db, obj_in={**offer, "product_id": product_id})
                    new_offer_ids.add(offer['id'])
                # This is based on assumption specified in the excersise description:
                # "Once an offer sells out, it disappears and is replaced by another offer."
                # delete removed offers - this could also be done in any other way,
                # for example by setting 'is_available' flag or some other method
                offer_ids_to_delete = [
                    str(offer.id) for offer
                    in crud.offer.get_multi_by_product(db, product_id = product_id)
                    if str(offer.id) not in new_offer_ids
                ]
                crud.offer.remove_multiple_by_id(db, ids=offer_ids_to_delete)
                return 'Succeeded'
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
    with SessionLocal() as db:
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
