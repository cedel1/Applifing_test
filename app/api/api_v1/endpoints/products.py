import logging
from typing import List
from uuid import UUID

import httpx
from app import crud, schemas
from app.api import deps
from app.api.offer_api_auth import auth_token
from app.core.celery_app import celery_app
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from tenacity import after_log, before_log, retry, retry_if_result, stop_after_attempt, wait_fixed, wait_random

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
            print(jsonable_encoder(product_in))
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
    registered_product_response: dict = Depends(register_product_in_offer_service),
) -> schemas.Product:
    """
    Create a new product.
    """
    if registered_product_response.status_code != 201:
        raise HTTPException(status_code=registered_product_response.status_code)

    try:
        if registered_product_response.json()['id'] == str(product_in.id):
            product = crud.product.create(db=db, obj_in=product_in)
            celery_app.send_task("app.worker.download_offers_for_product", args=[str(product_in.id)])
        else:
            raise HTTPException(status_code=400, detail="External API returned different product id than expected")
    except httpx.RequestError as exception:
        raise HTTPException(status_code=400, detail=str(exception))
    except httpx.HTTPStatusError as exception:
        raise HTTPException(status_code=exception.response.status_code, detail=str(exception))

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
    id: UUID
) -> schemas.Product:
    """
    Delete a product from the database.
    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    crud.product.remove(db=db, id=id)
    return product
