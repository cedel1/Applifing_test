from typing import List

from sqlalchemy.orm import Session

from app.models.offer import Offer
from app.schemas.offer import OfferCreate, OfferUpdate

from .base import CRUDBase


class CRUDOffer(CRUDBase[Offer, OfferCreate, OfferUpdate]):
    def get_multi_by_product(
        self, db: Session, *, product_id: int, skip: int = 0, limit: int = 100
    ) -> List[Offer]:
        return (
            db.query(self.model)
            .filter(Offer.product_id == product_id)
            .order_by(Offer.price.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )


offer = CRUDOffer(Offer)
