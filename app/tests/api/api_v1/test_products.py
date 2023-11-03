from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.tests.conftest import client, db
from app.tests.utils.product import create_random_product


def test_product_should_be_created(
    client: TestClient, db: Session) -> None:
    data = {"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bdd", "name": "Bar", "description": "Dancers"}
    response = client.post(f"{settings.API_V1_STR}/products/", json=data)
    assert response.status_code == 201
    content = response.json()
    assert content["id"] == data["id"]
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]


def test_product_should_be_retrieved(
    client: TestClient, db: Session) -> None:
    product = create_random_product(db)
    response = client.get(f"{settings.API_V1_STR}/products/{product.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(product.id)
    assert content["name"] == product.name
    assert content["description"] == product.description
