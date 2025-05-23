from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.wine import (
    Wine as WineSchema,
    WineList,
    WineSearch,
    WineSearchList,
)

from app.schemas.wine_id_list_response import WineListByCountryResponse

from app.services.wine_service import (
    get_wine_by_id,
    get_wines_paginated,
    get_wine_details_by_country,
    search_wines,
    fetch_variety_list,
)

router = APIRouter(
    prefix="/api/wines",
    tags=["wines"],
)


@router.get("/variety-list", response_model=List[str])
def get_variety_list(db: Session = Depends(get_db)) -> List[str]:
    """
    Get a list of unique wine varieties.
    """
    return fetch_variety_list(db)


@router.get("/{wine_id}", response_model=WineSchema)
def get_wine(wine_id: int, db: Session = Depends(get_db)):
    """
    Get a specific wine by ID
    """
    wine = get_wine_by_id(db, wine_id)
    if wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return wine


@router.get("/", response_model=WineList)
def get_wines(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
):
    """
    Get a paginated list of wines
    """
    return get_wines_paginated(db=db, page=page, size=size)


@router.get("/by-country/{country}", response_model=WineListByCountryResponse)
def get_wines_by_country_endpoint(
    country: str = Path(..., description="Country to fetch wines for"),
    limit: int = Query(100, ge=1, le=1000),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    db: Session = Depends(get_db),
):
    """
    Get a paginated list of wine details for a specific country.
    """
    return get_wine_details_by_country(
        db=db, country=country, limit=limit, cursor=cursor
    )


@router.post("/search", response_model=WineSearchList)
def search_wines_endpoint(
    search_params: WineSearch,
    db: Session = Depends(get_db),
):
    """
    Search and filter wines based on various criteria
    """
    return search_wines(db=db, params=search_params)
