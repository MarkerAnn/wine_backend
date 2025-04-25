from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.bucket_wines import BucketWinesResponse
from app.services.bucket_wines_service import fetch_wines_in_bucket

router = APIRouter()


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

    Uses cursor-based pagination for efficient retrieval of large datasets.

    Parameters:
    - price_min: Minimum price for the bucket
    - price_max: Maximum price for the bucket
    - points_min: Minimum points for the bucket
    - points_max: Maximum points for the bucket
    - cursor: Pagination cursor (optional)
    - limit: Number of results per page

    Returns:
    - BucketWinesResponse: List of wines and pagination info
    """
    try:
        return fetch_wines_in_bucket(
            db=db,
            price_min=price_min,
            price_max=price_max,
            points_min=points_min,
            points_max=points_max,
            cursor=cursor,
            limit=limit,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
