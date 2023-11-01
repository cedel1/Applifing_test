from uuid import UUID

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.product import ProductCreate

from .utils import random_lower_string, random_uuid


def create_random_product(db: Session, id: UUID=None, name:str=None, description:str=None) -> models.Product:
    product_in =  ProductCreate(id=id or random_uuid(), name=name or random_lower_string(),
                                description=description or random_lower_string())
    return crud.product.create(db=db, obj_in=product_in)
