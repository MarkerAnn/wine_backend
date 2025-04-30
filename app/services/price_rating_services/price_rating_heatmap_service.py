from typing import Optional
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from app.models.wine import Wine
from app.schemas.price_rating_aggregated import HeatmapResponse, WineExample


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
