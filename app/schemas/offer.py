from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Shared properties
class OfferBase(BaseModel):
    price: Optional[int] = None
    items_in_stock: Optional[int] = None
    product_id: Optional[UUID] = None


class OfferCreate(OfferBase):
    id: UUID
    price: int
    items_in_stock: int
    product_id: UUID


class OfferUpdate(OfferBase):
    pass


# Properties shared by models stored in DB
class OfferInDBBase(OfferBase):
    id: UUID
    price: int
    items_in_stock: int
    product_id: UUID
    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Offer(OfferBase):
    pass


# Properties stored in DB
class OfferInDB(OfferInDBBase):
    pass
