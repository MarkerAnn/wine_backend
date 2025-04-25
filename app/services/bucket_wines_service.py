from typing import Optional, Tuple, List
import base64
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.wine import Wine
from app.schemas.bucket_wines import (
    WineInBucket,
    BucketWinesPagination,
    BucketWinesResponse,
)


def fetch_wines_in_bucket(
    db: Session,
    price_min: float,
    price_max: float,
    points_min: int,
    points_max: int,
    cursor: Optional[str] = None,
    limit: int = 10,
) -> BucketWinesResponse:
    """
    Fetch wines within a specific price and points range with pagination.

    Args:
        db: Database session
        price_min: Minimum price for the bucket
        price_max: Maximum price for the bucket
        points_min: Minimum points for the bucket
        points_max: Maximum points for the bucket
        cursor: Pagination cursor (optional)
        limit: Number of results per page

    Returns:
        BucketWinesResponse: List of wines and pagination info
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

    # Process cursor if provided, cursorbased pagination. Decode to get the last_id and filter
    # the query to only include wines with id greater than last_id
    last_id = None
    if cursor:
        cursor_data = json.loads(base64.b64decode(cursor).decode("utf-8"))
        last_id = cursor_data.get("last_id")
        if last_id:
            query = query.filter(Wine.id > last_id)

    # Order by id and limit results
    query = query.order_by(Wine.id).limit(
        limit + 1
    )  # Get one extra to check if there are more

    # Execute query
    wines = query.all()

    # Process pagination and format results
    wine_list, pagination = _process_pagination_and_format(wines, limit)

    return BucketWinesResponse(
        wines=wine_list, pagination=pagination, total=total_count
    )


# Define a private function to handle pagination and formatting ('_')
def _process_pagination_and_format(
    wines: List[Wine], limit: int
) -> Tuple[List[WineInBucket], BucketWinesPagination]:
    """
    Process pagination and format wine results.

    Args:
        wines: List of Wine objects from database
        limit: Results limit per page

    Returns:
        Tuple containing formatted wine list and pagination info
    """
    # Check if there are more results
    has_next = len(wines) > limit
    if has_next:
        wines = wines[:limit]  # Remove the extra item

    # Prepare next cursor if there are more results
    next_cursor = None
    if has_next and wines:
        last_wine = wines[-1]
        cursor_data = {"last_id": getattr(last_wine, "id", 0)}
        next_cursor = base64.b64encode(json.dumps(cursor_data).encode("utf-8")).decode(
            "utf-8"
        )

    # Format wine objects to schema model
    wine_list: List[WineInBucket] = []  # Explicit typing of the list
    for wine in wines:
        # Safely extract values using getattr with defaults
        wine_id = getattr(wine, "id", 0)
        wine_title = getattr(wine, "title", None)
        wine_winery = getattr(wine, "winery", None)
        wine_price = getattr(wine, "price", None)
        wine_points = getattr(wine, "points", None)
        wine_country = getattr(wine, "country", None)
        wine_variety = getattr(wine, "variety", None)

        # Create WineInBucket instance with proper type conversions
        wine_list.append(
            WineInBucket(
                id=int(wine_id) if wine_id is not None else 0,
                name=str(wine_title) if wine_title is not None else f"Wine {wine_id}",
                winery=str(wine_winery) if wine_winery is not None else "",
                price=float(wine_price) if wine_price is not None else 0.0,
                points=int(wine_points) if wine_points is not None else 0,
                country=str(wine_country) if wine_country is not None else None,
                variety=str(wine_variety) if wine_variety is not None else None,
            )
        )

    # Create pagination info
    pagination = BucketWinesPagination(next_cursor=next_cursor, has_next=has_next)

    return wine_list, pagination
