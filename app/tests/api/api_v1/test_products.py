from typing import Dict

from app import crud
from app.api.api_v1.endpoints.products import register_product_in_offer_service
from app.core.celery_app import celery_app
from app.core.config import settings
from app.main import app
from app.models import Offer, Product
from app.tests.conftest import get_mocked_celery
from app.tests.utils.offer import create_random_offer
from app.tests.utils.overrides import (
    override_register_product_in_offer_service_returns_201,
    override_register_product_in_offer_service_returns_401,
    override_register_product_in_offer_service_returns_409,
    override_register_product_in_offer_service_returns_422)
from app.tests.utils.product import create_random_product
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_multiple_product_should_be_read(
      client: TestClient, db: Session, clear_db_products: None) -> None:
    product1 = create_random_product(db=db)
    product2 = create_random_product(db=db)
    response = client.get(f"{settings.API_V1_STR}/products/")
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 2
    assert content[0]["id"] == str(product1.id)
    assert content[0]["name"] == product1.name
    assert content[0]["description"] == product1.description
    assert content[1]["id"] == str(product2.id)
    assert content[1]["name"] == product2.name
    assert content[1]["description"] == product2.description


def test_product_should_react_to_401_response_from_product_registration_service(
      client: TestClient, db: Session, normal_user_token_headers: Dict[str, str]) -> None:
    app.dependency_overrides[register_product_in_offer_service] = override_register_product_in_offer_service_returns_401
    data = {"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bee", "name": "Bar", "description": "Dancers"}
    response = client.post(f"{settings.API_V1_STR}/products/", json=data, headers=normal_user_token_headers)

    assert response.status_code == 401
    content = response.json()
    assert content["detail"] == "Unauthorized"
    assert not crud.product.get(db, id="3135dcd5-7add-4a27-b669-4f44b9aa9bee")


def test_product_creation_should_fail_if_already_saved_and_registered_409_response_from_product_registration_service(
      client: TestClient, db: Session, normal_user_token_headers: Dict[str, str]) -> None:
    app.dependency_overrides[register_product_in_offer_service] = override_register_product_in_offer_service_returns_409
    create_random_product(db, id="3135dcd5-7add-4a27-b669-4f44b9aa9baa")
    data = {"id": "3135dcd5-7add-4a27-b669-4f44b9aa9baa", "name": "Bar", "description": "Dancers"}
    response = client.post(f"{settings.API_V1_STR}/products/", json=data, headers=normal_user_token_headers)

    assert response.status_code == 409
    content = response.json()
    assert content["detail"] == "Product already registered"
    product = crud.product.get(db, id="3135dcd5-7add-4a27-b669-4f44b9aa9baa")
    assert str(product.id) == "3135dcd5-7add-4a27-b669-4f44b9aa9baa"


def test_product_should_be_recreated_after_product_already_registered_409_response_from_product_registration_service(
      client: TestClient, db: Session, normal_user_token_headers: Dict[str, str]) -> None:
    app.dependency_overrides[register_product_in_offer_service] = override_register_product_in_offer_service_returns_409
    data = {"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bee", "name": "Bar", "description": "Dancers"}
    response = client.post(f"{settings.API_V1_STR}/products/", json=data, headers=normal_user_token_headers)

    assert response.status_code == 201
    product = crud.product.get(db, id="3135dcd5-7add-4a27-b669-4f44b9aa9bee")
    assert str(product.id) == "3135dcd5-7add-4a27-b669-4f44b9aa9bee"
    assert product.name == "Bar"
    assert product.description == "Dancers"


def test_product_should_react_to_422_response_from_product_registration_service(
      client: TestClient, db: Session, normal_user_token_headers: Dict[str, str]) -> None:
    app.dependency_overrides[register_product_in_offer_service] = override_register_product_in_offer_service_returns_422
    data = {"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bbb", "name": "Bar", "description": "Dancers"}
    response = client.post(f"{settings.API_V1_STR}/products/", json=data, headers=normal_user_token_headers)

    assert response.status_code == 422
    content = response.json()
    assert content["detail"] == "Unprocessable Entity"
    assert not crud.product.get(db, id="3135dcd5-7add-4a27-b669-4f44b9aa9bbb")


def test_product_should_be_created(
      client: TestClient, normal_user_token_headers: Dict[str, str], monkeypatch) -> None:
    app.dependency_overrides[register_product_in_offer_service] = override_register_product_in_offer_service_returns_201
    monkeypatch.setattr(celery_app, "send_task", get_mocked_celery)

    data = {"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bdd", "name": "Bar", "description": "Dancers"}
    response = client.post(f"{settings.API_V1_STR}/products/", json=data, headers=normal_user_token_headers)

    assert response.status_code == 201
    content = response.json()
    assert content["id"] == data["id"]
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]


def test_product_should_not_be_created_if_user_is_unauthorized(
      client: TestClient, monkeypatch) -> None:
    app.dependency_overrides[register_product_in_offer_service] = override_register_product_in_offer_service_returns_201
    monkeypatch.setattr(celery_app, "send_task", get_mocked_celery)

    data = {"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bee", "name": "Bar", "description": "Dancers"}
    response = client.post(f"{settings.API_V1_STR}/products/", json=data)

    assert response.status_code == 401
    content = response.json()
    assert content["detail"] == "Not authenticated"


def test_product_read_should_return_product(
      client: TestClient, db: Session) -> None:
    product = create_random_product(db=db)
    response = client.get(f"{settings.API_V1_STR}/products/{product.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(product.id)
    assert content["name"] == product.name
    assert content["description"] == product.description


def test_product_read_should_return_not_found_if_product_does_not_exist(
      client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/products/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    response_content = response.json()
    assert response_content["detail"] == "Product not found"


def test_product_should_be_updated(
      client: TestClient, db: Session, normal_user_token_headers: Dict[str, str]) -> None:
    product = create_random_product(db=db)
    data = {"name": "Bar", "description": "Dancers"}
    response = client.put(f"{settings.API_V1_STR}/products/{product.id}", json=data, headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(product.id)
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]


def test_product_should_not_be_updated_for_unauthenticated_user(
      client: TestClient, db: Session) -> None:
    product = create_random_product(db=db)
    data = {"name": "Bar", "description": "Dancers"}
    response = client.put(f"{settings.API_V1_STR}/products/{product.id}", json=data)
    assert response.status_code == 401
    content = response.json()
    assert content["detail"] == "Not authenticated"


def test_product_id_should_not_be_updated(
      client: TestClient, db: Session, normal_user_token_headers: Dict[str, str]) -> None:
    product = create_random_product(db=db)
    data = {"id": "3135dcd5-7add-4a27-b669-4f44b9aa9bdd"}
    response = client.put(f"{settings.API_V1_STR}/products/{product.id}", json=data, headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(product.id)


def test_product_update_should_return_not_found_if_product_does_not_exist(
      client: TestClient, normal_user_token_headers: Dict[str, str]) -> None:
    data = {"name": "Bar", "description": "Dancers"}
    response = client.put(f"{settings.API_V1_STR}/products/00000000-0000-0000-0000-000000000000",
                          json=data, headers=normal_user_token_headers)
    assert response.status_code == 404
    response_content = response.json()
    assert response_content["detail"] == "Product not found"


def test_product_should_be_removed(
      client: TestClient, db: Session, normal_user_token_headers: Dict[str, str]) -> None:
    product = create_random_product(db=db)
    response = client.delete(f"{settings.API_V1_STR}/products/{product.id}", headers=normal_user_token_headers)
    assert response.status_code == 200


def test_product_should_not_be_removed_if_user_is_unauthenticated(
      client: TestClient, db: Session) -> None:
    product = create_random_product(db=db)
    response = client.delete(f"{settings.API_V1_STR}/products/{product.id}")
    assert response.status_code == 401
    response_content = response.json()
    assert response_content["detail"] == "Not authenticated"


def test_product_delete_should_return_not_found_if_product_does_not_exist(
      client: TestClient, normal_user_token_headers: Dict[str, str]) -> None:
    response = client.delete(f"{settings.API_V1_STR}/products/00000000-0000-0000-0000-000000000000",
                             headers=normal_user_token_headers)
    assert response.status_code == 404
    contetn = response.json()
    assert contetn["detail"] == "Product not found"


def test_product_should_be_removed_including_related_offers(
      client: TestClient, db: Session, normal_user_token_headers: Dict[str, str]) -> None:
    product = create_random_product(db=db)
    offer = create_random_offer(db=db, product_id=product.id)

    response = client.delete(f"{settings.API_V1_STR}/products/{product.id}", headers=normal_user_token_headers)
    assert response.status_code == 200
    assert product not in db.query(Product).all()
    assert offer not in db.query(Offer).all()


def test_product_offers_should_be_returned(
      client: TestClient, db: Session) -> None:
    product = create_random_product(db=db)
    create_random_offer(db=db, product_id=product.id)
    create_random_offer(db=db, product_id=product.id)
    response = client.get(f"{settings.API_V1_STR}/products/{product.id}/offers")
    assert response.status_code == 200
    response_content = response.json()
    assert len(response_content) == 2
    assert response_content[0]["product_id"] == str(product.id)
    assert response_content[1]["product_id"] == str(product.id)


def test_product_offers_should_return_empty_list_if_no_offers_exist(
      client: TestClient, db: Session) -> None:
    product = create_random_product(db=db)
    response = client.get(f"{settings.API_V1_STR}/products/{product.id}/offers")
    assert response.status_code == 200
    response_content = response.json()
    assert len(response_content) == 0
    assert isinstance(response_content, list)


def test_product_offers_should_return_not_found_if_product_does_not_exist(
      client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/products/00000000-0000-0000-0000-000000000000/offers")
    assert response.status_code == 404
    response_content = response.json()
    assert response_content["detail"] == "Product not found"
