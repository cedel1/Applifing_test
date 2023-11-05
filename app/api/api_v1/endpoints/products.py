from typing import List
from uuid import UUID

import httpx
from app import crud, schemas
from app.api import deps
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.Product]
)
def read_products(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100
) -> List[schemas.Product]:
    """
    Retrieves a list of products from the database.

    Parameters:
        db (Session): The database session to use.
        skip (int): The number of products to skip.
        limit (int): The maximum number of products to retrieve.

    Returns:
        List[schemas.Product]: A list of product objects.
    """
    return crud.product.get_multi(db=db, skip=skip, limit=limit)


def _register_product_caller(product: schemas.ProductCreate) -> None:
    """
    This function is responsible for registering a product.

    Args:
        product (schemas.ProductCreate): The product to be registered.

    Returns:
        None: The response from the product registration API call.

    Raises:
        HTTPStatusError: If the product registration API call returns an error status code.
    """
    headers = {'Bearer': settings.AUTHENTICATION_TOKEN}
    product_register_response = httpx.post(f"{settings.OFFER_SERVICE_BASE_URL}/api/v1/products/register",
                                           headers=headers,
                                           json=jsonable_encoder(product))
    product_register_response.raise_for_status()


def _get_authentication_token() -> None:
    headers = {'Bearer': settings.OFFER_SERVICE_TOKEN}
    auth_response = httpx.post(f"{settings.OFFER_SERVICE_BASE_URL}/api/v1/auth", headers=headers)
    auth_response.raise_for_status()
    settings.AUTHENTICATION_TOKEN = auth_response.json()['access_token']


def _register_product_in_offer_service(product: schemas.ProductCreate) -> None:
    """
    Registers a product in the offer service.

    Args:
        product (schemas.ProductCreate): The JSON representation of the product to be registered.

    Returns:
        None: Returns nothing.

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
) -> schemas.Product:
    """
    Create a new product.

    Parameters:
        db (Session): The database session.
        product_in (schemas.ProductCreate): The input data for creating the product.

    Returns:
        Any: The created product.

    Raises:
        HTTPException: If there is an error during the request.
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
) -> schemas.Product:
    """
    Update a product in the database.

    Args:
        db (Session): The database session.
        id (UUID): The ID of the product to update.
        product_in (ProductUpdate): The updated product data.

    Returns:
        schemas.Product: The updated product.

    Raises:
        HTTPException: If the product with the given ID is not found.

    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return crud.item.update(db=db, db_obj=product, obj_in=product_in)


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

    Arguments:
    - `db` (Session): The database session object.
    - `id` (UUID): The ID of the product to retrieve.

    Returns:
    - `Product`: The retrieved product.

    Raises:
    - `HTTPException`: If the product with the given ID is not found.
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

    Parameters:
        - db (Session): The database session dependency.
        - id (UUID): The ID of the product.

    Returns:
        - List[schemas.Offer]: A list of offer schemas.
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

    Parameters:
        - db (Session): The database session.
        - id (UUID): The ID of the product to be deleted.

    Returns:
        - Product: The deleted product.

    Raises:
        - HTTPException(404): If the product is not found in the database.
    """
    product = crud.product.get(db=db, id=id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    crud.product.remove(db=db, id=id)
    return product
