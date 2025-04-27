from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.bucket_wines import BucketWinesResponse
from app.services.bucket_wines_service import fetch_wines_in_bucket

router = APIRouter(
    prefix="/api/wines/bucket",
    tags=["list-wines-in-bucket"],
)

@router.get("/{price_min}/{price_max}/{points_min}/{points_max}", response_model=BucketWinesResponse)
def get_wines_in_bucket_by_range(
    price_min: float,
    price_max: float,
    points_min: int,
    points_max: int,
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(10, description="Number of results per page", ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    Get paginated list of wines in a specific price-rating bucket.
    Designed for click-interactions on the heatmap.
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
