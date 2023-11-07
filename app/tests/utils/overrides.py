import httpx
from app import schemas
from app.api.offer_api_auth import auth_token
from fastapi import Depends

from .test_db import TestingSessionLocal


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_auth_token():
    return "3fa85f64-5717-4562-b3fc-2c963f66afa6"


def override_register_product_in_offer_service_returns_201(
        product_in: schemas.ProductCreate,
        auth_token: str = Depends(auth_token)
) -> httpx.Response:
    return httpx.Response(201, json={"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bdd"})


def override_register_product_in_offer_service_returns_401(
        product_in: schemas.ProductCreate,
        auth_token: str = Depends(auth_token)
) -> httpx.Response:
    return httpx.Response(401, json={"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bee"})


def override_register_product_in_offer_service_returns_422(
        product_in: schemas.ProductCreate,
        auth_token: str = Depends(auth_token)
) -> httpx.Response:
    return httpx.Response(422, json={"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bff"})

