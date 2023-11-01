from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.Offer])
def read_offers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve offers.
    """
    return crud.offer.get_multi(db, skip=skip, limit=limit)

@router.get(
    "/{id}",
    response_model=schemas.Offer,
    responses={404: {"model": schemas.NotFoundResponse}})
def read_offer(
    *,
    db: Session = Depends(deps.get_db),
    id: UUID,
) -> Any:
    """
    Get offer by ID.
    """
    offer = crud.offer.get(db=db, id=id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer
