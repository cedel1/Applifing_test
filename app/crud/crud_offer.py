from typing import List
from uuid import UUID

from app.core.config import settings
from app.models.offer import Offer
from app.schemas.offer import OfferCreate, OfferUpdate
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .base import CRUDBase


class CRUDOffer(CRUDBase[Offer, OfferCreate, OfferUpdate]):
    def get_multi_by_product(
        self, db: Session, *, product_id: str, skip: int = 0, limit: int = settings.API_MAX_RECORDS_LIMIT
    ) -> List[Offer]:
        return (
            db.query(self.model)
            .filter(Offer.product_id == str(product_id))
            .order_by(Offer.price.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def bulk_create_or_update(self, db: Session, *, objects: List[OfferCreate]) -> None:
        # this is postgres specific, but should be way faster for large datasets than doing it in SQLAlchemy ORM
        # database agnostic way
        statement = insert(Offer).values(objects)
        statement = statement.on_conflict_do_update(
            index_elements=[Offer.id],
            set_=dict(
                id=statement.excluded.id,
                price=statement.excluded.price,
                items_in_stock=statement.excluded.items_in_stock,
                product_id=statement.excluded.product_id))
        db.execute(statement)
        db.commit()

    def remove_multiple_by_id(self, db: Session, *, ids: List[UUID]) -> None:
        db.query(self.model).filter(self.model.id.in_(ids)).delete(synchronize_session="fetch")
        db.commit()


offer = CRUDOffer(Offer)
