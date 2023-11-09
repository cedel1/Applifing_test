import httpx
from app import crud
from app.api.offer_api_auth import auth_token
from app.core.celery_app import celery_app
from app.core.config import settings
from fastapi import HTTPException
from sqlalchemy.orm import Session


def _get_number_of_batches(number_of_products: int) -> str:
    number_of_batches = 1
    if number_of_products > settings.API_MAX_RECORDS_LIMIT:
        number_of_batches = (
            number_of_products // settings.API_MAX_RECORDS_LIMIT
            + (1 if ((number_of_products % settings.API_MAX_RECORDS_LIMIT) > 0) else 0))
    return number_of_batches


def do_download_offers_for_product(db: Session, product_id: str) -> str:
    try:
        with httpx.Client() as client:
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
            return f"Created or updated {len(offers)} offers, deleted {len(offer_ids_to_delete)} offers."
    except (httpx.HTTPError, KeyError, ValueError, HTTPException):
        raise Exception(f"Task download_offers_for_product({product_id}) failed")


def do_download_product_offers(db: Session) -> str:
    number_of_products = crud.product.get_number_of_products(db=db)
    number_of_batches = _get_number_of_batches(number_of_products)

    for i in range(number_of_batches):
        product_only_ids_result = crud.product.get_multi_id(db=db, skip=i * settings.API_MAX_RECORDS_LIMIT,
                                                            limit=settings.API_MAX_RECORDS_LIMIT)
        for product in product_only_ids_result:
            celery_app.send_task("app.celery.worker.download_offers_for_product", args=[str(product.id)])
    return f"Send tasks to update offers for {number_of_products} product(s)."

