from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.bucket_wines import BucketWinesResponse
from app.services.bucket_wines_service import fetch_wines_in_bucket

router = APIRouter(
    prefix="/api/wines/bucket",
    tags=["bucket-wines"],
)


def _fetch_bucket(
    price_min: float,
    price_max: float,
    points_min: int,
    points_max: int,
    cursor: Optional[str],
    limit: int,
    db: Session,
):
    """Shared logic for fetching bucket wines."""
    return fetch_wines_in_bucket(
        db=db,
        price_min=price_min,
        price_max=price_max,
        points_min=points_min,
        points_max=points_max,
        cursor=cursor,
        limit=limit,
    )


@router.get("/", response_model=BucketWinesResponse)
def get_wines_in_bucket(
    price_min: float = Query(..., description="Minimum price for the bucket"),
    price_max: float = Query(..., description="Maximum price for the bucket"),
    points_min: int = Query(..., description="Minimum points for the bucket"),
    points_max: int = Query(..., description="Maximum points for the bucket"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(10, description="Number of results per page", ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of wines in a specific price-rating bucket.

    Query-param version.
    """
    return _fetch_bucket(
        price_min, price_max, points_min, points_max, cursor, limit, db
    )
