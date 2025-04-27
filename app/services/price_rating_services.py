from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, cast, Integer, Numeric

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
    price_bucket_size: float,  # The size of the price bucket (e.g. 10.0 for 10–20kr)
    points_bucket_size: int,  # The size of the points bucket (e.g. 1 for 85–86 points)
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
    # Calculate price_bucket in SQL with FLOOR-function
    price_bucket_expr = func.floor(Wine.price / price_bucket_size) * price_bucket_size
    # Calculatte points_bucket in SQL with FLOOR-function
    points_bucket_expr = (
        func.floor(Wine.points / points_bucket_size) * points_bucket_size
    )

    # Start the base query with required fields and only include rows where price, points and country exist
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

    # Create aggregated query so calculations are done in SQL/DB
    agg_query = base_query.with_entities(
        price_bucket_expr.label("price_min"),
        points_bucket_expr.label("points_min"),
        func.count().label("count"),
    ).group_by("price_min", "points_min")

    # Get the aggregated results
    # Only get the bucket, not the actual wines
    agg_results = agg_query.all()

    # prepare the bucket for response, empty list
    buckets = []

    # For each aggregated bucket, create a new PriceRatingBucket object
    # and add it to the list
    for result in agg_results:
        price_min = float(result.price_min)
        points_min = int(result.points_min)
        count = result.count

        # Get some example wines for this bucket, up to 3
        example_query = base_query.filter(
            func.floor(Wine.price / price_bucket_size) * price_bucket_size == price_min,
            func.floor(Wine.points / points_bucket_size) * points_bucket_size
            == points_min,
        ).limit(3)
        examples = example_query.all()

        # Create examples of wines for this bucket, 3.
        example_list = []
        for wine in examples:
            example = WineExample(
                name=getattr(wine, "title", f"Wine {wine.id}"),
                price=float(wine.price),
                points=int(wine.points),
                winery=str(wine.winery),
            )
            example_list.append(example)

        # Create a bucket and add to list
        bucket = PriceRatingBucket(
            price_min=price_min,
            price_max=price_min + price_bucket_size,
            points_min=points_min,
            points_max=points_min + points_bucket_size,
            count=count,
            examples=example_list,
        )
        buckets.append(bucket)

    # Return the response model with the list of buckets
    return AggregatedPriceRatingResponse(
        buckets=buckets,
        total_wines=total_wines,
        bucket_size={"price": float(price_bucket_size), "points": points_bucket_size},
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
    # Define bucket expressions for price and points
    price_bucket_expr = func.floor(Wine.price / price_bucket_size) * price_bucket_size
    points_bucket_expr = (
        func.floor(Wine.points / points_bucket_size) * points_bucket_size
    )

    # Basequery with filter
    base_query = db.query(Wine).filter(
        and_(Wine.price.isnot(None), Wine.points.isnot(None), Wine.country.isnot(None))
    )

    # Add additional filters
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

    # Count all wines after filter
    total_wines = base_query.count()

    # Aggregation query for heatmap
    agg_query = base_query.with_entities(
        price_bucket_expr.label("price_min"),
        points_bucket_expr.label("points_min"),
        func.count().label("count"),
        func.avg(Wine.price).label("avg_price"),  # För hover-info
        func.min(Wine.price).label("min_price"),  # För hover-info
        func.max(Wine.price).label("max_price"),  # För hover-info
    ).group_by("price_min", "points_min")

    # Get the aggregated results
    agg_results = agg_query.all()

    # Prepare the data structure for heatmap
    x_categories = sorted({float(r.price_min) for r in agg_results})
    y_categories = sorted({r.points_min for r in agg_results})
    max_count = max((r.count for r in agg_results), default=0)

    data = []
    bucket_map = {}

    # Build heatmap data and bucket map
    for r in agg_results:
        x_idx = x_categories.index(float(r.price_min))
        y_idx = y_categories.index(r.points_min)
        key = f"{r.price_min}-{r.points_min}"

        # Get top 3 varieties(druvsorter) for this bucket
        variety_query = (
            base_query.filter(
                func.floor(Wine.price / price_bucket_size) * price_bucket_size
                == r.price_min,
                func.floor(Wine.points / points_bucket_size) * points_bucket_size
                == r.points_min,
            )
            .with_entities(Wine.variety, func.count().label("variety_count"))
            .group_by(Wine.variety)
            .order_by(func.count().desc())
            .limit(3)
        )
        top_varieties = [
            {"variety": v.variety, "count": v.variety_count}
            for v in variety_query.all()
        ]

        # Build bucket map with hoover info
        bucket_map[key] = {
            "price_min": float(r.price_min),
            "price_max": float(r.price_min) + price_bucket_size,
            "points_min": r.points_min,
            "points_max": r.points_min + points_bucket_size,
            "count": r.count,
            "avg_price": round(float(r.avg_price), 2),
            "price_range": f"${float(r.min_price):.2f} - ${float(r.max_price):.2f}",
            "top_varieties": top_varieties,
        }

        # Build heatmap data array
        data.append([x_idx, y_idx, r.count])

    return HeatmapResponse(
        data=data,
        x_categories=x_categories,
        y_categories=y_categories,
        bucket_map=bucket_map,
        max_count=max_count,
        total_wines=total_wines,
        bucket_size={"price": float(price_bucket_size), "points": points_bucket_size},
    )
