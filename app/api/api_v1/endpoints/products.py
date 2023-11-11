import logging
from typing import List
from uuid import UUID

import httpx
from app import crud, models, schemas
from app.api import deps
from app.api.offer_api_auth import auth_token
from app.core.celery_app import celery_app
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from tenacity import (after_log, before_log, retry, retry_if_result,
                      stop_after_attempt, wait_fixed, wait_random)

router = APIRouter()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.get(
    "/",
    response_model=List[schemas.Product]
)
def read_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = settings.API_MAX_RECORDS_LIMIT
) -> List[schemas.Product]:
    """
    Retrieves a list of products from the database.
    """
    return crud.product.get_multi(db=db, skip=skip, limit=limit)


def _should_retry_registration(value):
    return (
        value == httpx.HTTPStatusError
        and value.response.status_code == 401
        and auth_token.refresh_access_token())


@retry(
    retry=retry_if_result(_should_retry_registration),
    stop=stop_after_attempt(2),
    wait=wait_fixed(1),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def register_product_in_offer_service(
        product_in: schemas.ProductCreate,
        auth_token: str = Depends(auth_token)
) -> httpx.Response:
    try:
        with httpx.Client() as client:
            headers = {"Bearer": auth_token}
            product_register_response = client.post(f"{settings.OFFER_SERVICE_BASE_URL}api/v1/products/register",
                                                   headers=headers,
                                                   json=jsonable_encoder(product_in))
            return product_register_response
    except httpx.RequestError as exception:
        raise HTTPException(status_code=400, detail=str(exception))


@router.post(
    "/",
    response_model=schemas.Product,
    status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: schemas.ProductCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    registered_product_response: dict = Depends(register_product_in_offer_service),
) -> schemas.Product:
    """
    Create a new product.
    """
    # Some error from external API we cannot recover from
    if registered_product_response.status_code not in {201, 409}:
        raise HTTPException(status_code=registered_product_response.status_code)

    # returned and sent ids not matching for HTTP created status (409 does not return id)
    if (
        registered_product_response.status_code == 201
        and registered_product_response.json()['id'] != str(product_in.id)
    ):
        raise HTTPException(
            status_code=400,
            detail=f"External API returned different product id than expected. \
            The returned id was {registered_product_response.json()['id']}"
        )

    # product is registered in remote service and we also have it locally
    if registered_product_response.status_code == 409 and crud.product.exists(db, id=product_in.id):
        raise HTTPException(status_code=registered_product_response.status_code, detail="Product already registered")

    # Now the product is registered in remote service and not registered locally. There are two possible cases why this
    # might happen:
    #
    # - it is either beiing registered for the first time
    # - it was registered before but deleted localy later on (and it stayed registered and in the remote service
    #   as that does not have delete/unregister functionality)
    #
    #   It is a bit risky to handle the second case like this and relies on the fact that product ids are immutable -
    #   one id can only mean one and the same product (ie. the same id cannot be repurpose for different products).
    #   If that was not the case, than when remote service returns 409, the product should not be saved locally.
    #   On the other hand, that would also mean that once the product was delete locally, it could never be
    #   re-registered again. That could be solved by not allowing to delete the product locally (only marking it
    #   as deleted, but keeping it in db) - but that would bring other problems when creating a new product with
    #   the same id.
    #   The best solution would probably be to not allow DELETE method on products at all, only deactivating
    #   them by setting a "is_available" property on them. Then if POST with the same product.id was called,
    #   it would return 409 - Conflict response.
    product = crud.product.create(db=db, obj_in=product_in)
    celery_app.send_task("app.celery.worker.download_offers_for_product", args=[str(product_in.id)])

    return product


@router.put(
    "/{id}",
    response_model=schemas.Product,
    responses={404: {"model": schemas.NotFoundResponse}})
def update_product(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    product_in: schemas.ProductUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.Product:
    """
    Update a product in the database.
    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.product.update(db=db, db_obj=product, obj_in=product_in)


@router.get(
    "/{id}",
    response_model=schemas.Product,
    responses={404: {"model": schemas.NotFoundResponse}}
)
def read_product(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID
) -> schemas.Product:
    """
    Retrieve a specific product by its ID.
    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get(
    "/{id}/offers",
    response_model=List[schemas.Offer],
    responses={404: {"model": schemas.NotFoundResponse}}  # add response to OpenAPI schema
)
def read_product_offers(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
) -> List[schemas.Offer]:
    """
    Retrieve a list of offers for a specific product.
    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    offers = crud.offer.get_multi_by_product(db=db, product_id=product.id)
    return offers


@router.delete(
    "/{id}",
    response_model=schemas.Product,
    responses={404: {"model": schemas.NotFoundResponse}}
)
def delete_product(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> schemas.Product:
    """
    Delete a product from the database.
    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    crud.product.remove(db=db, id=id)
    return product
