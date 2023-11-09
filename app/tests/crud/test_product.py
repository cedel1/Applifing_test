from sqlalchemy.orm import Session

from app import crud
from app.schemas.product import ProductCreate, ProductUpdate
from app.tests.utils.product import create_random_product
from app.tests.utils.utils import random_lower_string, random_uuid


def test_create_product(db: Session) -> None:
    id = random_uuid()
    name = random_lower_string()
    description = random_lower_string()
    product_in = ProductCreate(id=id, name=name, description=description)
    product = crud.product.create(db=db, obj_in=product_in)
    assert product.id == id
    assert product.name == name
    assert product.description == description


def test_get_product(db: Session) -> None:
    product = create_random_product(db)
    stored_product = crud.product.get(db=db, id=product.id)
    assert stored_product
    assert product.id == stored_product.id
    assert product.name == stored_product.name
    assert product.description == stored_product.description


def test_update_product(db: Session) -> None:
    product = create_random_product(db)
    description2 = random_lower_string()
    product_update = ProductUpdate(description=description2)
    product2 = crud.product.update(db=db, db_obj=product, obj_in=product_update)
    assert product.id == product2.id
    assert product.name == product2.name
    assert product2.description == description2


def test_delete_product(db: Session) -> None:
    id = random_uuid()
    name = random_lower_string()
    description = random_lower_string()
    product_in = ProductCreate(id=id, name=name, description=description)
    product = crud.product.create(db=db, obj_in=product_in)
    product2 = crud.product.remove(db=db, id=product.id)
    product3 = crud.product.get(db=db, id=product2.id)
    assert product3 is None
    assert product2.id == id
    assert product2.name == name
    assert product2.description == description


def test_get_number_of_products_should_return_number_of_products(db: Session, clear_db_products) -> None:
    product_count = 5
    for _ in range(product_count):
        create_random_product(db)
    assert crud.product.get_number_of_products(db=db) == product_count
