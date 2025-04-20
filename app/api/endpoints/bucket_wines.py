# app/api/endpoints/bucket_wines.py
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
import base64
import json

from app.db.database import get_db
from app.models.wine import Wine
from app.schemas.bucket_wines import (
    BucketWinesResponse,
    BucketWinesPagination,
    WineInBucket,
)

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
    # Base query with bucket filters
    query = db.query(Wine).filter(
        and_(
            Wine.price >= price_min,
            Wine.price < price_max,
            Wine.points >= points_min,
            Wine.points < points_max,
        )
    )

    # Get total count for this bucket
    total_count = query.count()

    # Apply cursor-based pagination if a cursor is provided
    last_id = None
    if cursor:
        try:
            # Decode the cursor (base64 encoded JSON with last_id)
            cursor_data = json.loads(base64.b64decode(cursor).decode("utf-8"))
            last_id = cursor_data.get("last_id")
            if last_id:
                query = query.filter(Wine.id > last_id)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid cursor: {str(e)}")

    # Order by id and limit results
    query = query.order_by(Wine.id).limit(
        limit + 1
    )  # Get one extra to check if there are more

    # Execute query
    wines = query.all()

    # Check if there are more results
    has_next = len(wines) > limit
    if has_next:
        wines = wines[:limit]  # Remove the extra item

    # Prepare next cursor if there are more results
    next_cursor = None
    if has_next and wines:
        last_wine = wines[-1]
        cursor_data = {"last_id": last_wine.id}
        next_cursor = base64.b64encode(json.dumps(cursor_data).encode("utf-8")).decode(
            "utf-8"
        )

    # Format response
    wine_list = [
        WineInBucket(
            id=wine.id,
            name=(
                wine.title
                if hasattr(wine, "title") and wine.title
                else f"Wine {wine.id}"
            ),
            winery=wine.winery,
            price=float(wine.price),
            points=wine.points,
            country=wine.country,
            variety=wine.variety,
        )
        for wine in wines
    ]

    # Prepare pagination info
    pagination = BucketWinesPagination(next_cursor=next_cursor, has_next=has_next)

    return BucketWinesResponse(
        wines=wine_list, pagination=pagination, total=total_count
    )
