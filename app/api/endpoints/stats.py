# stats.py
from typing import List, Dict, Any, cast, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func


from app.db.database import get_db
from app.models.wine import Wine
from app.schemas.country_stats import CountryStats, CountriesStatsList, VarietyInfo
from app.schemas.price_rating import PriceRatingResponse, PriceRatingDataPoint

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
    # Query for basic country statistics
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
        wine_count = int(country_data.count)  # Convert to int explicitly

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

        # Create CountryStats object
        country_stats = CountryStats(
            country=country_name,
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


@router.get("/stats/price-rating", response_model=PriceRatingResponse)
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
        Wine.price.isnot(None)
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
