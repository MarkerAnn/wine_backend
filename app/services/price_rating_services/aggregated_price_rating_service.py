from typing import Optional, List
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from app.models.wine import Wine
from app.schemas.price_rating_aggregated import (
    AggregatedPriceRatingResponse,
    PriceRatingBucket,
)


# ------------------------------------------
# Aggregate wines into buckets by price/points
# ------------------------------------------
def fetch_aggregated_price_rating(
    db: Session,
    price_bucket_size: float,  # The size of the price bucket (e.g. 10.0 for 10–20$)
    points_bucket_size: int,  # The size of the points bucket (e.g. 1 for 85–86 points)
    country: Optional[str],
    variety: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    min_points: Optional[int],
    max_points: Optional[int],
    page: Optional[int],
    page_size: Optional[int],
) -> AggregatedPriceRatingResponse:
    """
    Group wines into "buckets" (e.g. 10–20kr, 85–90 points) and count them.
    Also include up to 3 example wines per bucket.
    """

    # Validate bucket sizes
    if price_bucket_size <= 0:
        raise ValueError("price_bucket_size must be greater than 0")
    if points_bucket_size <= 0:
        raise ValueError("points_bucket_size must be greater than 0")

    # Validate pagination (if provided)
    if page is not None and page < 1:
        raise ValueError("Page number must be at least 1")
    if page_size is not None and page_size < 1:
        raise ValueError("Page size must be at least 1")

    # Validate price range
    if (
        min_price is not None
        and max_price is not None
        and min_price > max_price
    ):
        raise ValueError(
            f"Invalid price range: min_price={min_price}, max_price={max_price}"
        )

    # Validate points range
    if (
        min_points is not None
        and max_points is not None
        and min_points > max_points
    ):
        raise ValueError(
            f"Invalid points range: min_points={min_points}, max_points={max_points}"
        )

    # Calculate price_bucket in SQL with FLOOR-function
    price_bucket_expr = func.floor(Wine.price / price_bucket_size) * price_bucket_size
    # Calculatte points_bucket in SQL with FLOOR-function
    points_bucket_expr = (
        func.floor(Wine.points / points_bucket_size) * points_bucket_size
    )

    # Start the base query with required fields and only include 
    # rows where price, points and country exist
    base_query = db.query(Wine).filter(
        and_(Wine.price.isnot(None), Wine.points.isnot(None), Wine.country.isnot(None))
    )

    # Add filters to the base query
    if country:
        base_query = base_query.filter(Wine.country == country)
    if variety:
        base_query = base_query.filter(Wine.variety == variety)
    if min_price is not None:
        base_query = base_query.filter(Wine.price >= min_price)
    if max_price is not None:
        base_query = base_query.filter(Wine.price <= max_price)
    if min_points is not None:
        base_query = base_query.filter(Wine.points >= min_points)
    if max_points is not None:
        base_query = base_query.filter(Wine.points <= max_points)

    # Count how many wines after filter
    total_wines = base_query.count()

    # 1. Create aggregated query so calculations are done in SQL/DB
    agg_query = base_query.with_entities(
        price_bucket_expr.label("price_min"),
        points_bucket_expr.label("points_min"),
        func.count().label("count"),
    ).group_by("price_min", "points_min")

    # 2. Sort in the database
    agg_query = agg_query.order_by("price_min", "points_min")

    # 3. Count total buckets (for metadata)
    total_buckets = agg_query.count()

    # 4. Get the specific page or all results
    if page is not None and page_size is not None:
        agg_results = agg_query.offset((page - 1) * page_size).limit(page_size).all()
    else:
        agg_results = agg_query.all()

    # prepare the bucket for response, empty list
    buckets: List[PriceRatingBucket] = []

    # For each aggregated bucket, create a new PriceRatingBucket object
    # and add it to the list
    for price_min_val, points_min_val, bucket_count in agg_results:
        bucket = PriceRatingBucket(
            price_min=float(price_min_val),
            price_max=float(price_min_val) + price_bucket_size,
            points_min=int(points_min_val),
            points_max=int(points_min_val) + points_bucket_size,
            count=bucket_count,
        )
        buckets.append(bucket)

    # An extra query is needed to get the total number of buckets
    total_buckets = agg_query.count()

    # REturn the current page of buckets
    return AggregatedPriceRatingResponse(
        buckets=buckets,
        total_wines=total_wines,
        total_buckets=total_buckets,
        bucket_size={"price": float(price_bucket_size), "points": points_bucket_size},
    )
