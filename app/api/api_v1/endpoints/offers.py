from typing import List
from uuid import UUID

from app import crud, schemas
from app.api import deps
from app.core.config import settings
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/",
    response_model=List[schemas.Offer])
def read_offers(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = settings.API_MAX_RECORDS_LIMIT,
) -> List[schemas.Offer]:
    """
    A function that reads a list of offers from the database.

    Parameters:
    - db (Session): The database session.
    - skip (int, optional): The number of offers to skip. Defaults to 0.
    - limit (int, optional): The maximum number of offers to retrieve. Defaults to 100.

    Returns:
    - List[schemas.Offer]: A list of offer objects retrieved from the database.
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
) -> schemas.Offer:
    """
    Retrieves an offer from the database based on the specified ID.

    Parameters:
        - db: The database session dependency.
        - id: The ID of the offer to retrieve.

    Returns:
        - An instance of schemas.Offer representing the retrieved offer.

    Raises:
        - HTTPException(404): If the offer with the specified ID is not found in the database.
    """
    offer = crud.offer.get(db=db, id=id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer
