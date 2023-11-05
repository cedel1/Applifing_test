from typing import Dict, Generator

import httpx
import pytest
from app import schemas
from app.api.api_v1.endpoints.products import register_product_in_offer_service
from app.api.deps import get_db
from app.api.offer_api_auth import auth_token
from app.core.config import settings
from app.db.base import Base
from app.db.init_db import init_db
from app.main import app
from app.models import Offer, Product
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import get_superuser_token_headers
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session
from sqlalchemy_utils.functions import create_database, database_exists

from .utils.overrides import override_auth_token, override_get_db
from .utils.test_db import TestingSessionLocal, engine

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[auth_token] = override_auth_token


def mock_register_product_in_offer_service(
        product_in: schemas.ProductCreate,
        auth_token: str = Depends(auth_token)
) -> httpx.Response:
    return httpx.Response(201, json={"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bdd"})


app.dependency_overrides[register_product_in_offer_service] = mock_register_product_in_offer_service


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator:
    # It is also a bit tricky, since we are dealing with at least two connection - one from engine and one from session.
    # These connections need to be cleaned up separately and their commanduse not mixed, otherwise database connection
    # locks will happen.
    if not database_exists(str(settings.SQLALCHEMY_TESTING_DATABASE_URI)):
        create_database(str(settings.SQLALCHEMY_TESTING_DATABASE_URI))
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    init_db(db)
    yield db
    db.close()

    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def clear_db_products(db: Session) -> None:
    db.execute(delete(Offer))
    db.execute(delete(Product))
    db.commit()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> Dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> Dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
