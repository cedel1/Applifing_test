from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.offer import OfferCreate

from .product import create_random_product
from .utils import random_int, random_uuid


def create_random_offer(db: Session, id: UUID=None, price: int=None, items_in_stock: int=None,
                         product_id: UUID=None) -> models.Offer:
    return crud.offer.create(
        db=db,
        obj_in=OfferCreate(
            id=id or random_uuid(),
            price=price or random_int(),
            items_in_stock=items_in_stock or random_int(),
            product_id=product_id or None))


def create_random_offer_with_product(db: Session, id: UUID=None, price: int=None, items_in_stock: int=None,
                                      product:models.Product=None) -> models.Offer:
    return create_random_offer(db=db, id=id, price=price, items_in_stock=items_in_stock,
                               product_id=create_random_product(db).id)
