from typing import Optional, List
from sqlalchemy import func, and_, cast, Numeric
from sqlalchemy.orm import Session
from app.models.wine import Wine
from app.schemas.price_rating_aggregated import BucketExamplesResponse, WineExample


# ---------------------------------------------
# Fetch example wines from a specific bucket
# ---------------------------------------------
def fetch_bucket_examples(
    db: Session,
    price_min: float,
    points_min: int,
    price_bucket_size: float,
    points_bucket_size: int,
    country: Optional[str] = None,
    variety: Optional[str] = None,
    limit: int = 3,
) -> BucketExamplesResponse:
    """
    Fetch example wines for a specific price/rating bucket.
    This is separated from the main aggregation query for performance.
    """
    # Base query with filter
    query = db.query(Wine).filter(
        and_(
            Wine.price.isnot(None),
            Wine.points.isnot(None),
            Wine.country.isnot(None),
        )
    )

    # Add filter to match the bucket
    query = query.filter(
        cast(func.floor(Wine.price / price_bucket_size) * price_bucket_size, Numeric)
        == price_min,
        cast(func.floor(Wine.points / points_bucket_size) * points_bucket_size, Numeric)
        == points_min,
    )

    # Add other filters
    if country:
        query = query.filter(Wine.country == country)
    if variety:
        query = query.filter(Wine.variety == variety)

    # Count the total number of wines in this bucket
    count = query.count()

    # Get example wines (3 per bucket)
    examples = query.limit(limit).all()

    # Create a list of WineExample objects

    example_list: List[WineExample] = []
    for wine in examples:
        example = WineExample(
            name=getattr(wine, "title", f"Wine {wine.id}"),
            price=float(wine.price) if wine.price is not None else 0.0, # type: ignore
            points=int(wine.points) if wine.points is not None else 0,
            winery=str(wine.winery),
        )
        example_list.append(example)

    # Return example with metadata
    return BucketExamplesResponse(
        price_min=price_min,
        price_max=price_min + price_bucket_size,
        points_min=points_min,
        points_max=points_min + points_bucket_size,
        count=count,
        examples=example_list,
    )
