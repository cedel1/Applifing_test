from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Uuid
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .offer import Offer # noqa: F401


class Product(Base):
    id = Column(Uuid, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, index=True, nullable=False)
    offers = relationship("Offer", back_populates="product")
