from typing import TYPE_CHECKING

from app.db.base_class import Base
from sqlalchemy import Column, ForeignKey, Integer, Uuid
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from .product import Product  # noqa: F401


class Offer(Base):
    id = Column(Uuid, primary_key=True, index=True)
    price = Column(Integer, index=False, nullable=False)
    items_in_stock = Column(Integer, index=False, nullable=False)
    product_id = Column(Uuid, ForeignKey("product.id"), index=True, nullable=False)
    product = relationship("Product", back_populates="offers")
