from typing import List

from app.core.config import settings
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from sqlalchemy.orm import Session

from .base import CRUDBase


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    def get_multi_id(
        self, db: Session, *, skip: int = 0, limit: int = settings.API_MAX_RECORDS_LIMIT
    ) -> List[Product.id]:
        return db.query(self.model.id).offset(skip).limit(limit).all()

    def get_number_of_products(self, db: Session) -> int:
        return db.query(self.model).count()


product = CRUDProduct(Product)
