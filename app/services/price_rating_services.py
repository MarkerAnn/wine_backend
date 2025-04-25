# app/services/price_rating_service.py

from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.wine import Wine
from app.schemas.price_rating import PriceRatingResponse, PriceRatingDataPoint
from app.schemas.price_rating_aggregated import (
    AggregatedPriceRatingResponse,
    PriceRatingBucket,
    WineExample,
    HeatmapResponse,
)

# -------------------------
# Fetch raw wine datapoints
# -------------------------
def fetch_price_rating(
    db: Session,
    country: Optional[str],
    variety: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    min_points: Optional[int],
    max_points: Optional[int],
    page: int,
    page_size: int,
) -> PriceRatingResponse:
    """
    Fetch wine data filtered by price and rating.
    Each datapoint is used for a scatterplot (price vs rating).
    """
    # Start the query with required fields and only include rows where price and country exist
    query = db.query(
        Wine.id, Wine.price, Wine.points, Wine.country, Wine.variety, Wine.winery
    ).filter(Wine.price.isnot(None), Wine.country.isnot(None))

    # Apply filters if they are given, so we can use them in the query (e.g. country, variety)
    if country:
        query = query.filter(Wine.country == country)
    if variety:
        query = query.filter(Wine.variety == variety)
    if min_price is not None:
        query = query.filter(Wine.price >= min_price)
    if max_price is not None:
        query = query.filter(Wine.price <= max_price)
    if min_points is not None:
        query = query.filter(Wine.points >= min_points)
    if max_points is not None:
        query = query.filter(Wine.points <= max_points)

    # Count how many wines match before we limit it for pagination
    # This is important for the frontend to know how many pages there are
    total = query.count()

    # Apply pagination and fetch results
    wines = query.offset((page - 1) * page_size).limit(page_size).all()

    # Convert to Pydantic response model using correct Python types to match the pydantic schema
    data: List[PriceRatingDataPoint] = [
        PriceRatingDataPoint(
            id=wine.id,
            price=float(wine.price),
            points=int(wine.points),
            country=str(wine.country),
            variety=str(wine.variety),
            winery=str(wine.winery),
        )
        for wine in wines
    ]

    # Return the final response
    return PriceRatingResponse(data=data, total=total, page=page, page_size=page_size)

# ------------------------------------------
# Aggregate wines into buckets by price/points
# ------------------------------------------
def fetch_aggregated_price_rating(
    db: Session,
    price_bucket_size: float, # The size of the price bucket (e.g. 10.0 for 10–20kr)
    points_bucket_size: int, # The size of the points bucket (e.g. 1 for 85–86 points)
    country: Optional[str],
    variety: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    min_points: Optional[int],
    max_points: Optional[int],
) -> AggregatedPriceRatingResponse:
    """
    Group wines into "buckets" (e.g. 10–20kr, 85–90 points) and count them.
    Also include up to 3 example wines per bucket.
    """
    price_bucket = Decimal(price_bucket_size)  # Use Decimal for precision in math

    # Start query: we only want wines with price, points and country set
    query = db.query(Wine).filter(
        and_(Wine.price.isnot(None), Wine.points.isnot(None), Wine.country.isnot(None))
    )

    # Apply filters
    if country:
        query = query.filter(Wine.country == country)
    if variety:
        query = query.filter(Wine.variety == variety)
    if min_price is not None:
        query = query.filter(Wine.price >= min_price)
    if max_price is not None:
        query = query.filter(Wine.price <= max_price)
    if min_points is not None:
        query = query.filter(Wine.points >= min_points)
    if max_points is not None:
        query = query.filter(Wine.points <= max_points)

    total_wines = query.count()  # Count total wines after filters

    # Create buckets: key = (price_min, points_min), value = dict with bucket info
    buckets: Dict[Tuple[Decimal, int], Dict[str, Any]] = {}

    # For each wine in the query, calculate the bucket it belongs to
    # and add it to the corresponding bucket
    for wine in query.all():
        price_val = float(getattr(wine, 'price', 0))  # use getattr to avoid NoneType error
        points_val = int(getattr(wine, 'points', 0)) 

        # Devision, if price is 230 and the bucket size is 100, the result is 230 / 100 = 2, 2 * 100 = 200 -> The wine is in the 200–300 bucket
        price_min = (Decimal(price_val) // price_bucket) * price_bucket
        points_min = (points_val // points_bucket_size) * points_bucket_size
        key = (price_min, points_min)

        bucket = buckets.setdefault(
            key,
            {
                "price_min": price_min,
                "price_max": price_min + price_bucket,
                "points_min": points_min,
                "points_max": points_min + points_bucket_size,
                "count": 0,
                "examples": [],
            },
        )

        bucket["count"] += 1

        # Add up to 3 example wines in each bucket
        if len(bucket["examples"]) < 3:
            example = WineExample(
                name=getattr(wine, "title", f"Wine {wine.id}"),
                price=price_val,
                points=points_val,
                winery=str(wine.winery),
            )
            bucket["examples"].append(example)

    # Convert the dictonary with buckets to a list of PriceRatingBucket objects
    price_buckets: List[PriceRatingBucket] = [
        PriceRatingBucket(
            price_min=b["price_min"],
            price_max=b["price_max"],
            points_min=b["points_min"],
            points_max=b["points_max"],
            count=b["count"],
            examples=b["examples"],
        )
        for b in buckets.values()
    ]

    # Return all the buckets, total wines and bucket size
    return AggregatedPriceRatingResponse(
        buckets=price_buckets,
        total_wines=total_wines,
        bucket_size={"price": float(price_bucket), "points": points_bucket_size},
    )

# ---------------------------------------------
# Prepare heatmap-friendly structure from buckets
# ---------------------------------------------
def fetch_price_rating_heatmap(
    db: Session,
    price_bucket_size: float,
    points_bucket_size: int,
    country: Optional[str],
    variety: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    min_points: Optional[int],
    max_points: Optional[int],
) -> HeatmapResponse:
    """
    Prepare heatmap format from aggregated buckets for use in frontend charts.
    """
    # Call the aggregation function to get the buckets
    # This is the same as fetch_aggregated_price_rating, but we need to format it for the heatmap
    agg = fetch_aggregated_price_rating(
        db=db,
        price_bucket_size=price_bucket_size,
        points_bucket_size=points_bucket_size,
        country=country,
        variety=variety,
        min_price=min_price,
        max_price=max_price,
        min_points=min_points,
        max_points=max_points,
    )

    # A sorted list with all the unique price_min values (x-axis)
    # A sorted list with all the unique points_min values (y-axis)
    # The maximum count of wines in any bucket (For the heatmap color scale)
    x_categories = sorted({float(b.price_min) for b in agg.buckets})
    y_categories = sorted({b.points_min for b in agg.buckets})
    max_count = max((b.count for b in agg.buckets), default=0)

    data: List[List[int]] = []
    bucket_map: Dict[str, Dict[str, Any]] = {}

    for b in agg.buckets:
        x_idx = x_categories.index(float(b.price_min)) # Find the index postition of the price_min in the x_categories list
        y_idx = y_categories.index(b.points_min) # Find the index postition of the points_min in the y_categories list
        key = f"{b.price_min}-{b.points_min}"

        bucket_map[key] = {
            "price_min": float(b.price_min),
            "price_max": float(b.price_max),
            "points_min": b.points_min,
            "points_max": b.points_max,
            "count": b.count,
            "examples": b.examples,
        }

        data.append([x_idx, y_idx, b.count])

    return HeatmapResponse(
        data=data,
        x_categories=x_categories,
        y_categories=y_categories,
        bucket_map=bucket_map,
        max_count=max_count,
        total_wines=agg.total_wines,
        bucket_size=agg.bucket_size,
    )
