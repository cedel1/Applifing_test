from sqlalchemy.orm import Session

from app import crud
from app.schemas.offer import OfferCreate, OfferUpdate
from app.tests.utils.offer import create_random_offer_with_product
from app.tests.utils.product import create_random_product
from app.tests.utils.utils import random_int, random_uuid


def test_create_offer(db: Session) -> None:
    id = random_uuid()
    price = random_int()
    items_in_stock = random_int()
    offer_product = create_random_product(db)
    offer_in = OfferCreate(id=id, price=price, items_in_stock=items_in_stock, product_id=offer_product.id)
    offer = crud.offer.create(db=db, obj_in=offer_in)
    assert offer.id == id
    assert offer.price == price
    assert offer.items_in_stock == items_in_stock


def test_get_offer(db: Session) -> None:
    offer = create_random_offer_with_product(db=db)
    stored_offer = crud.offer.get(db=db, id=offer.id)
    assert stored_offer
    assert offer.id == stored_offer.id
    assert offer.price == stored_offer.price
    assert offer.items_in_stock == stored_offer.items_in_stock
    assert offer.product_id == stored_offer.product_id


def test_update_offer(db: Session) -> None:
    offer = create_random_offer_with_product(db=db)
    items_in_stock2 = random_int()
    offer_update = OfferUpdate(items_in_stock=items_in_stock2)
    offer2 = crud.offer.update(db=db, db_obj=offer, obj_in=offer_update)
    assert offer.id == offer2.id
    assert offer.price == offer2.price
    assert offer2.items_in_stock == items_in_stock2
    assert offer2.product_id == offer.product_id
