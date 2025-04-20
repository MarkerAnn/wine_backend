# stats.py
from typing import List, Dict, Any, cast, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func


from app.db.database import get_db
from app.models.wine import Wine
from app.schemas.country_stats import CountryStats, CountriesStatsList, VarietyInfo
from app.schemas.price_rating import PriceRatingResponse, PriceRatingDataPoint
from app.schemas.price_rating_aggregated import (
    WineExample,
    PriceRatingBucket,
    AggregatedPriceRatingResponse,
    HeatmapResponse,
)
from app.utils.country_mapping import get_geojson_country_name


router = APIRouter()


@router.get("/countries", response_model=CountriesStatsList)
async def get_countries_stats(
    db: Session = Depends(get_db),
    min_wines: int = Query(
        50, description="Minimum number of wines per country to include"
    ),
) -> Dict[str, Any]:
    """
    Get aggregated wine statistics by country

    Parameters:
    - min_wines: Filter out countries with fewer wines than this threshold

    Returns:
    - CountriesStatsList: List of countries with their wine statistics
    """
    # Query for basic country statistics (oförändrad)
    country_stats_query = (
        db.query(
            Wine.country,
            func.avg(Wine.points).label("avg_points"),
            func.count(Wine.id).label("count"),  # pylint: disable=E1102
            func.min(Wine.price).label("min_price"),
            func.max(Wine.price).label("max_price"),
            func.avg(Wine.price).label("avg_price"),
        )
        .filter(Wine.country.isnot(None))  # Filter out wines with no country
        .group_by(Wine.country)
        .having(
            func.count(Wine.id) >= min_wines  # pylint: disable=E1102
        )  # Only include countries with enough wines
        .order_by(func.count(Wine.id).desc())  # pylint: disable=E1102
        .all()
    )

    # Create result list to return
    countries_data: List[CountryStats] = []

    # For each country, we need to find the top varieties
    for country_data in country_stats_query:
        country_name = country_data.country
        wine_count = int(country_data.count)

        # Apply mapping to get the GeoJSON country name
        geojson_country_name = get_geojson_country_name(country_name)

        # Query for top varieties in this country
        variety_query = (
            db.query(
                Wine.variety, func.count(Wine.id).label("count")
            )  # pylint: disable=E1102
            .filter(Wine.country == country_name, Wine.variety.isnot(None))
            .group_by(Wine.variety)
            .order_by(func.count(Wine.id).desc())  # pylint: disable=E1102
            .limit(5)  # Limit to top 5 varieties
            .all()
        )

        # Convert to list of VarietyInfo objects
        top_varieties: List[VarietyInfo] = []
        for variety_data in variety_query:
            variety_count = int(variety_data.count)  # Convert to int explicitly
            percentage = (variety_count / wine_count) * 100
            variety_info = VarietyInfo(
                name=variety_data.variety,
                count=variety_count,
                percentage=round(percentage, 2),
            )
            top_varieties.append(variety_info)

        # Create CountryStats object with the mapped GeoJSON country name
        country_stats = CountryStats(
            country=geojson_country_name,  # Använd det mappade namnet här
            original_country=country_name,  # Lägg till originalet för referens (se schema-ändring nedan)
            avg_points=round(float(country_data.avg_points), 2),
            count=wine_count,
            min_price=country_data.min_price,
            max_price=country_data.max_price,
            avg_price=(
                round(float(country_data.avg_price), 2)
                if country_data.avg_price
                else None
            ),
            top_varieties=top_varieties,
        )

        countries_data.append(country_stats)

    # Return the result matching the CountriesStatsList schema
    return {"items": countries_data, "total_countries": len(countries_data)}


@router.get("/price-rating", response_model=PriceRatingResponse)
async def get_price_rating_data(
    country: Optional[str] = None,
    variety: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_points: Optional[int] = None,
    max_points: Optional[int] = None,
    page: int = 1,
    page_size: int = 1000,
    db: Session = Depends(get_db),
):
    """
    Retrieve wine data for price vs rating scatterplot with optional filtering.

    Returns a collection of data points with price and rating information for visualization.
    """
    # Start building the query
    query = db.query(
        Wine.id, Wine.price, Wine.points, Wine.country, Wine.variety, Wine.winery
    ).filter(
        Wine.price.isnot(None), Wine.country.isnot(None)
    )  # Only include wines with price

    # Apply filters if provided
    if country:
        query = query.filter(Wine.country == country)
    if variety:
        query = query.filter(Wine.variety == variety)
    if min_price:
        query = query.filter(Wine.price >= min_price)
    if max_price:
        query = query.filter(Wine.price <= max_price)
    if min_points:
        query = query.filter(Wine.points >= min_points)
    if max_points:
        query = query.filter(Wine.points <= max_points)

    # Get total count for pagination
    total = query.count()

    # Apply pagination
    wines = query.offset((page - 1) * page_size).limit(page_size).all()

    # Convert to response model
    data = [
        PriceRatingDataPoint(
            id=wine.id,
            price=wine.price,
            points=wine.points,
            country=wine.country,
            variety=wine.variety,
            winery=wine.winery,
        )
        for wine in wines
    ]

    return PriceRatingResponse(data=data, total=total, page=page, page_size=page_size)


@router.get("/price-rating-aggregated", response_model=AggregatedPriceRatingResponse)
async def get_aggregated_price_rating_data(
    price_bucket_size: float = Query(10.0, description="Size of price range buckets"),
    points_bucket_size: int = Query(1, description="Size of points range buckets"),
    country: Optional[str] = None,
    variety: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_points: Optional[int] = None,
    max_points: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Retrieve aggregated wine data grouped into price-rating buckets.

    This endpoint aggregates wines into buckets based on price and rating ranges,
    significantly reducing data transfer while maintaining meaningful visualization.

    Parameters:
    - price_bucket_size: Size of each price range bucket (default: 10.0)
    - points_bucket_size: Size of each rating points bucket (default: 1)
    - country, variety, min/max price/points: Optional filters

    Returns:
    - AggregatedPriceRatingResponse: Buckets of wines with counts and examples
    """
    # Start building the query with filters
    query = db.query(Wine).filter(
        Wine.price.isnot(None), Wine.points.isnot(None), Wine.country.isnot(None)
    )

    # Convert price_bucket_size to Decimal
    price_bucket_size = Decimal(price_bucket_size)

    # Apply additional filters if provided
    if country:
        query = query.filter(Wine.country == country)
    if variety:
        query = query.filter(Wine.variety == variety)
    if min_price:
        query = query.filter(Wine.price >= min_price)
    if max_price:
        query = query.filter(Wine.price <= max_price)
    if min_points:
        query = query.filter(Wine.points >= min_points)
    if max_points:
        query = query.filter(Wine.points <= max_points)

    # Get overall count for metadata
    total_wines = query.count()

    # Create dictionary to store buckets
    # Key is a tuple of (price_min, points_min)
    buckets_dict = {}

    # Execute query and process wines
    wines = query.all()

    for wine in wines:
        # Determine which bucket this wine belongs to
        price_min = (Decimal(wine.price) // price_bucket_size) * price_bucket_size
        price_max = price_min + price_bucket_size

        points_min = int(wine.points // points_bucket_size) * points_bucket_size
        points_max = points_min + points_bucket_size

        # Create bucket key
        bucket_key = (price_min, points_min)

        # If this bucket doesn't exist yet, create it
        if bucket_key not in buckets_dict:
            buckets_dict[bucket_key] = {
                "price_min": price_min,
                "price_max": price_max,
                "points_min": points_min,
                "points_max": points_max,
                "count": 0,
                "examples": [],
                "examples_complete": False,
            }

        # Increment count
        buckets_dict[bucket_key]["count"] += 1

        # Add as example if we don't have enough examples yet
        if not buckets_dict[bucket_key]["examples_complete"]:
            if len(buckets_dict[bucket_key]["examples"]) < 3:
                example = WineExample(
                    name=wine.title if hasattr(wine, "title") else f"Wine {wine.id}",
                    price=wine.price,
                    points=wine.points,
                    winery=wine.winery,
                )
                buckets_dict[bucket_key]["examples"].append(example)

                # Mark as complete if we've collected 3 examples
                if len(buckets_dict[bucket_key]["examples"]) == 3:
                    buckets_dict[bucket_key]["examples_complete"] = True

    # Convert dictionary to list of PriceRatingBucket objects
    buckets = [
        PriceRatingBucket(
            price_min=data["price_min"],
            price_max=data["price_max"],
            points_min=data["points_min"],
            points_max=data["points_max"],
            count=data["count"],
            examples=data["examples"],
        )
        for data in buckets_dict.values()
    ]

    # Prepare and return response
    return AggregatedPriceRatingResponse(
        buckets=buckets,
        total_wines=total_wines,
        bucket_size={"price": price_bucket_size, "points": points_bucket_size},
    )


@router.get("/price-rating-heatmap", response_model=HeatmapResponse)
async def get_price_rating_heatmap(
    price_bucket_size: float = Query(10.0, description="Size of price range buckets"),
    points_bucket_size: int = Query(1, description="Size of points range buckets"),
    country: Optional[str] = None,
    variety: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_points: Optional[int] = None,
    max_points: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Retrieve pre-formatted heatmap data for visualizing price vs. rating distribution.

    This endpoint processes data on the server-side to match the exact format needed by
    frontend chart libraries, reducing client-side processing and improving performance.

    Parameters match the aggregated endpoint but return optimized visualization data.
    """
    query = db.query(Wine).filter(
        Wine.price.isnot(None), Wine.points.isnot(None), Wine.country.isnot(None)
    )

    # Convert price_bucket_size to Decimal
    price_bucket_size = Decimal(price_bucket_size)

    # Apply additional filters if provided
    if country:
        query = query.filter(Wine.country == country)
    if variety:
        query = query.filter(Wine.variety == variety)
    if min_price:
        query = query.filter(Wine.price >= min_price)
    if max_price:
        query = query.filter(Wine.price <= max_price)
    if min_points:
        query = query.filter(Wine.points >= min_points)
    if max_points:
        query = query.filter(Wine.points <= max_points)

    # Get total count for metadata
    total_wines = query.count()

    # Create dictionary to store buckets
    buckets_dict = {}

    # Execute query and process wines
    wines = query.all()

    for wine in wines:
        # Determine which bucket this wine belongs to
        price_min = (Decimal(wine.price) // price_bucket_size) * price_bucket_size
        price_max = price_min + price_bucket_size

        points_min = int(wine.points // points_bucket_size) * points_bucket_size
        points_max = points_min + points_bucket_size

        # Create bucket key
        bucket_key = (float(price_min), points_min)

        # If this bucket doesn't exist yet, create it
        if bucket_key not in buckets_dict:
            buckets_dict[bucket_key] = {
                "price_min": float(price_min),
                "price_max": float(price_max),
                "points_min": points_min,
                "points_max": points_max,
                "count": 0,
                "examples": [],
                "examples_complete": False,
            }

        # Increment count
        buckets_dict[bucket_key]["count"] += 1

        # Add as example if we don't have enough examples yet
        if not buckets_dict[bucket_key]["examples_complete"]:
            if len(buckets_dict[bucket_key]["examples"]) < 3:
                example = {
                    "name": wine.title if hasattr(wine, "title") else f"Wine {wine.id}",
                    "price": float(wine.price),
                    "points": wine.points,
                    "winery": wine.winery,
                }
                buckets_dict[bucket_key]["examples"].append(example)

                # Mark as complete if we've collected 3 examples
                if len(buckets_dict[bucket_key]["examples"]) == 3:
                    buckets_dict[bucket_key]["examples_complete"] = True

    # Prepare heatmap data for ECharts
    # First, get unique sorted categories for both axes
    x_categories = sorted(set(key[0] for key in buckets_dict.keys()))
    y_categories = sorted(set(key[1] for key in buckets_dict.keys()))

    # Find maximum count for color scaling
    max_count = (
        max(bucket["count"] for bucket in buckets_dict.values()) if buckets_dict else 0
    )

    # Create a map for lookup of original buckets (for tooltip etc.)
    bucket_map = {}

    # Transform data for heatmap
    heatmap_data = []
    for (price_min, points_min), bucket in buckets_dict.items():
        # Get indices for the categories
        x_index = x_categories.index(price_min)
        y_index = y_categories.index(points_min)

        # Create a key for bucket lookup
        key = f"{price_min}-{points_min}"
        bucket_map[key] = {
            "price_min": bucket["price_min"],
            "price_max": bucket["price_max"],
            "points_min": bucket["points_min"],
            "points_max": bucket["points_max"],
            "count": bucket["count"],
            "examples": bucket["examples"],
        }

        # Format data as [x, y, value] for ECharts
        heatmap_data.append([x_index, y_index, bucket["count"]])

    # Prepare and return response in the expected format for ECharts
    return HeatmapResponse(
        data=heatmap_data,
        x_categories=x_categories,
        y_categories=y_categories,
        bucket_map=bucket_map,
        max_count=max_count,
        total_wines=total_wines,
        bucket_size={"price": float(price_bucket_size), "points": points_bucket_size},
    )
