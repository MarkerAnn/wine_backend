import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.wine import Wine as WineModel
from app.schemas.wine import (
    Wine as WineSchema,
    WineList,
    WineSearch,
    WineSearchResult,
    WineSearchList,
)

router = APIRouter(
    prefix="/api/wines",
    tags=["wines"],
)


@router.get("/{wine_id}", response_model=WineSchema)
def get_wine(wine_id: int, db: Session = Depends(get_db)):
    """
    Get a specific wine by ID

    Parameters:
    - wine_id: The ID of the wine to retrieve

    Returns:
    - Wine: The wine object if found

    Raises:
    - HTTPException: If wine not found
    """
    wine = db.query(WineModel).filter(WineModel.id == wine_id).first()
    if wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return wine


# ...existing code...


@router.get("/", response_model=WineList)
def get_wines(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
) -> WineList:
    """
    Get a paginated list of wines

    Parameters:
    - page: The page number (starts at 1)
    - size: Number of items per page

    Returns:
    - WineList: Paginated list of wines
    """
    # Calculate offset
    skip = (page - 1) * size

    # Get total count
    total = db.query(WineModel).count()

    # Get wines for current page
    wines = db.query(WineModel).offset(skip).limit(size).all()

    # Map WineModel to WineSchema
    wine_schemas = [WineSchema.model_validate(wine) for wine in wines]

    # Calculate total pages
    pages = math.ceil(total / size)

    return WineList(items=wine_schemas, total=total, page=page, size=size, pages=pages)


@router.post("/search", response_model=WineSearchList)
def search_wines(
    search_params: WineSearch,
    db: Session = Depends(get_db),
) -> WineSearchList:
    """
    Search and filter wines based on various criteria

    Parameters:
    - search_params: The search and filter parameters

    Returns:
    - WineList: Paginated list of filtered wines
    """
    query = db.query(
        WineModel.id,
        WineModel.title,
        WineModel.price,
        WineModel.points,
        WineModel.country,
        WineModel.variety,
    )

    # Apply search filters. Use tsvector for full-text search
    if search_params.search:
        query = query.filter(
            WineModel.search_vector.match(
                search_params.search, postgresql_regconfig="english"
            )
        )

    if search_params.country:
        query = query.filter(WineModel.country == search_params.country)
    if search_params.variety:
        query = query.filter(WineModel.variety == search_params.variety)
    if search_params.min_price is not None:
        query = query.filter(WineModel.price >= search_params.min_price)
    if search_params.max_price is not None:
        query = query.filter(WineModel.price <= search_params.max_price)
    if search_params.min_points is not None:
        query = query.filter(WineModel.points >= search_params.min_points)
    if search_params.max_points is not None:
        query = query.filter(WineModel.points <= search_params.max_points)

    # Get total filtered count
    total = query.count()

    # Pagination
    skip = (search_params.page - 1) * search_params.size
    wines = query.offset(skip).limit(search_params.size).all()

    # When not getting an entire model from the database, we need to map the result like this
    wine_schemas = [
        WineSearchResult(
            id=wine.id,
            title=wine.title,
            price=wine.price,
            points=wine.points,
            country=wine.country,
            variety=wine.variety,
        )
        for wine in wines
    ]

    # Calculate total pages
    pages = math.ceil(total / search_params.size)

    return WineSearchList(
        items=wine_schemas,
        total=total,
        page=search_params.page,
        size=search_params.size,
        pages=pages,
    )
