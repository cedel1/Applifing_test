from sqlalchemy.orm import Session

from app import crud
from app.schemas.offer import OfferCreate, OfferUpdate
from app.tests.utils.offer import create_random_offer_with_product
from app.tests.utils.product import create_random_product
from app.tests.utils.utils import random_int, random_uuid


def test_create_offer_should_create_offer(db: Session) -> None:
    id = random_uuid()
    price = random_int()
    items_in_stock = random_int()
    offer_product = create_random_product(db)
    offer_in = OfferCreate(id=id, price=price, items_in_stock=items_in_stock, product_id=offer_product.id)
    offer = crud.offer.create(db=db, obj_in=offer_in)
    assert offer.id == id
    assert offer.price == price
    assert offer.items_in_stock == items_in_stock


def test_get_offer_should_retreive_offer(db: Session) -> None:
    offer = create_random_offer_with_product(db=db)
    stored_offer = crud.offer.get(db=db, id=offer.id)
    assert stored_offer
    assert offer.id == stored_offer.id
    assert offer.price == stored_offer.price
    assert offer.items_in_stock == stored_offer.items_in_stock
    assert offer.product_id == stored_offer.product_id


def test_update_offer_should_update_offer(db: Session) -> None:
    offer = create_random_offer_with_product(db=db)
    items_in_stock2 = random_int()
    offer_update = OfferUpdate(items_in_stock=items_in_stock2)
    offer2 = crud.offer.update(db=db, db_obj=offer, obj_in=offer_update)
    assert offer.id == offer2.id
    assert offer.price == offer2.price
    assert offer2.items_in_stock == items_in_stock2
    assert offer2.product_id == offer.product_id


def test_create_or_update_offer_should_create_offer(db: Session) -> None:
    product = create_random_product(db)
    current_offer_count = crud.offer.count(db)
    offer_update = OfferCreate(
        id=random_uuid(),
        price=random_int(),
        items_in_stock=random_int(),
        product_id=product.id)
    offer2 = crud.offer.create_or_update(db=db, obj_in=offer_update)
    assert offer_update.id == offer2.id
    assert offer_update.price == offer2.price
    assert offer_update.items_in_stock == offer2.items_in_stock
    assert offer_update.product_id == offer2.product_id
    assert current_offer_count + 1 == crud.offer.count(db)


def test_create_or_update_offer_should_update_offer(db: Session) -> None:
    offer = create_random_offer_with_product(db=db)
    offer_update_price = offer.price + 1
    offer_update_items_in_stock = offer.items_in_stock + 1
    current_offer_count = crud.offer.count(db)
    offer_update = OfferCreate(
        id=offer.id,
        price=offer_update_price,
        items_in_stock=offer_update_items_in_stock,
        product_id=offer.product.id)
    offer2 = crud.offer.create_or_update(db=db, obj_in=offer_update)
    assert offer_update.id == offer2.id
    assert offer2.id == offer.id
    assert offer_update.price == offer2.price
    assert offer2.price == offer_update_price
    assert offer_update.items_in_stock == offer2.items_in_stock
    assert offer2.items_in_stock == offer_update_items_in_stock
    assert offer_update.product_id == offer2.product_id
    assert offer2.product_id == offer.product.id
    assert current_offer_count == crud.offer.count(db)
