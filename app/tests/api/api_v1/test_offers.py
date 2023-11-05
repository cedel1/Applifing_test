from app.core.config import settings
from app.tests.utils.offer import create_random_offer
from app.tests.utils.product import create_random_product
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_offers_should_be_retrieved(
    client: TestClient, db: Session
) -> None:
    product = create_random_product(db=db)
    create_random_offer(db=db, product_id=product.id)
    create_random_offer(db=db, product_id=product.id)

    response = client.get(f"{settings.API_V1_STR}/offers/")
    assert response.status_code == 200
    response_content = response.json()
    assert len(response_content) == 2
    assert response_content[0]["product_id"] == str(product.id)
    assert response_content[1]["product_id"] == str(product.id)


def test_offer_should_be_retrieved_by_id(
    client: TestClient, db: Session
) -> None:
    product = create_random_product(db=db)
    offer1 = create_random_offer(db=db, product_id=product.id)

    response = client.get(f"{settings.API_V1_STR}/offers/{offer1.id}")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == str(offer1.id)
    assert content["price"] == offer1.price
    assert content["items_in_stock"] == offer1.items_in_stock
    assert content["product_id"] == str(offer1.product_id)

def test_read_offer_should_return_not_found_if_there_is_not_matching_offer(
    client: TestClient
) -> None:
    response = client.get(f"{settings.API_V1_STR}/offers/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Offer not found"
