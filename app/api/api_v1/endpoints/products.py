from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

import httpx
from app import crud, schemas
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.Product])
def read_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve product.
    """
    return crud.product.get_multi(db, skip=skip, limit=limit)


def _register_product_caller(product: schemas.ProductCreate) -> Any:
    headers = {'Bearer': settings.AUTHENTICATION_TOKEN}
    product_register_response = httpx.post(f"{settings.OFFER_SERVICE_BASE_URL}/api/v1/products/register",
                                           headers=headers,
                                           json=jsonable_encoder(product))
    product_register_response.raise_for_status()


def _get_authentication_token() -> Any:
    headers = {'Bearer': settings.OFFER_SERVICE_TOKEN}
    auth_response = httpx.post(f"{settings.OFFER_SERVICE_BASE_URL}/api/v1/auth", headers=headers)
    auth_response.raise_for_status()
    settings.AUTHENTICATION_TOKEN = auth_response.json()['access_token']


def _register_product_in_offer_service(product: schemas.ProductCreate) -> Any:
    """
    Registers a product in the offer service.

    Args:
        product (schemas.ProductCreate): The JSON representation of the product to be registered.

    Returns:
        Any: Returns nothing.

    Raises:
        HTTPException: If an HTTP status error occurs.
    """
    repeat = 0
    try:
        _register_product_caller(product)
    except httpx.HTTPStatusError as exception:
        if exception.response.status_code == 401 and repeat < 1:
            repeat += 1
            _get_authentication_token()
        else:
            raise HTTPException(status_code=exception.response.status_code, detail=str(exception))
    except httpx.RequestError as exception:
        raise HTTPException(status_code=400, detail=str(exception))


@router.post(
    "/",
    response_model=schemas.Product,
    status_code=status.HTTP_201_CREATED)
def create_product(
    *,
    db: Session = Depends(deps.get_db),
    product_in: schemas.ProductCreate,
) -> Any:
    """
    Create new Product and register it with service.
    """
    try:
        #_register_product_in_offer_service(product_in.model_dump())
        product = crud.product.create(db=db, obj_in=product_in)
#TODO: Trigger offer download for product just registered
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
) -> Any:
    """
    Update a product.
    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.item.update(db=db, db_obj=product, obj_in=product_in)


@router.get(
    "/{id}",
    response_model=schemas.Product,
    responses={404: {"model": schemas.NotFoundResponse}})
def read_product(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
) -> Any:
    """
    Get product by ID.
    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get(
    "/{id}/offers",
    response_model=schemas.Offer,
    responses={404: {"model": schemas.NotFoundResponse}})  # add response to OpenAPI
def read_product_offers(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
) -> Any:
    """
    Get product offers.
    """
    offers = crud.offer.get_multi_by_product(db=db, product_id=id)
    if not offers:
        raise HTTPException(status_code=404, detail="No offers found")
    return offers


@router.delete(
    "/{id}",
    response_model=schemas.Product,
    responses={404: {"model": schemas.NotFoundResponse}})
def delete_product(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
) -> Any:
    """
    Delete a product.
    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.product.remove(db=db, id=id)
