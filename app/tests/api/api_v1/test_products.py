from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Offer, Product
from app.tests.conftest import client, db
from app.tests.utils.offer import create_random_offer
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

def test_product_should_be_updated(
    client: TestClient, db: Session) -> None:
    product = create_random_product(db)
    data = {"name": "Bar", "description": "Dancers"}
    response = client.put(f"{settings.API_V1_STR}/products/{product.id}", json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(product.id)
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]


def test_product_id_should_not_be_updated(
    client: TestClient, db: Session) -> None:
    product = create_random_product(db)
    data = {"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bdd"}
    response = client.put(f"{settings.API_V1_STR}/products/{product.id}", json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(product.id)


def test_product_should_be_removed(
    client: TestClient, db: Session) -> None:
    product = create_random_product(db)
    response = client.delete(f"{settings.API_V1_STR}/products/{product.id}")
    assert response.status_code == 200


def test_product_should_be_removed_including_related_offers(
    client: TestClient, db: Session) -> None:
    product = create_random_product(db)
    offer = create_random_offer(db, product_id=product.id)

    response = client.delete(f"{settings.API_V1_STR}/products/{product.id}")
    assert response.status_code == 200
    assert product not in db.query(Product).all()
    assert offer not in db.query(Offer).all()


def test_product_offers_should_be_returned(
    client: TestClient, db: Session) -> None:
    product = create_random_product(db)
    create_random_offer(db, product_id=product.id)
    create_random_offer(db, product_id=product.id)

    response = client.get(f"{settings.API_V1_STR}/products/{product.id}/offers")
    assert response.status_code == 200
    response_content = response.json()
    assert len(response_content) == 2
    assert response_content[0]["product_id"] == str(product.id)
    assert response_content[1]["product_id"] == str(product.id)


#TODO: Test wrong response from registration service
