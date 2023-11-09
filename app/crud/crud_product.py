from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from sqlalchemy.orm import Session

from .base import CRUDBase


class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
    def get_number_of_products(self, db: Session) -> int:
        return db.query(self.model).count()


product = CRUDProduct(Product)
