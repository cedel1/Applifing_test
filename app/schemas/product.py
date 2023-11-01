from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Shared properties
class ProductBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# Properties to receive on product creation
class ProductCreate(ProductBase):
    id: UUID
    name: str
    description: str


# Properties to receive on product update
class ProductUpdate(ProductBase):
    pass


# Properties to receive on product delete
class ProductDelete(ProductBase):
    pass


# Properties shared by models stored in DB
class ProductInDBBase(ProductBase):
    id: UUID
    name: str
    description: str
    model_config = ConfigDict(from_attributes=True)


# Properties to return to client
class Product(ProductInDBBase):
    pass


# Properties stored in DB
class ProductInDB(ProductInDBBase):
    pass
