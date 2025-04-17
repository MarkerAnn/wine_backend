from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func


from app.db.database import get_db
from app.models.wine import Wine
from app.schemas.country_stats import CountryStats, CountriesStatsList, VarietyInfo

router = APIRouter()


@router.get("/countries", response_model=CountriesStatsList)
async def get_countries_stats(
    db: Session = Depends(get_db),
    min_wines: int = Query(
        50, description="Minimum number of wines per country to include"
    ),
):
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
            func.count(Wine.id).label("count"),
            func.min(Wine.price).label("min_price"),
            func.max(Wine.price).label("max_price"),
            func.avg(Wine.price).label("avg_price"),
        )
        .filter(Wine.country.isnot(None))  # Filter out wines with no country
        .group_by(Wine.country)
        .having(
            func.count(Wine.id) >= min_wines
        )  # Only include countries with enough wines
        .order_by(func.count(Wine.id).desc())  # Order by number of wines
        .all()
    )

    # Create result list to return
    countries_data = []

    # For each country, we need to find the top varieties
    for country_data in country_stats_query:
        country_name = country_data.country
        wine_count = country_data.count

        # Query fot op varieties in this country
        variety_query = (
            db.query(Wine.variety, func.count(Wine.id).label("count"))
            .filter(Wine.country == country_name, Wine.variety.isnot(None))
            .group_by(Wine.variety)
            .order_by(func.count(Wine.id).desc())
            .limit(5)  # Limit to top 5 varieties
            .all()
        )

        # Convert to list of VarietyInfo objects
        top_varieties = []
        for variety_data in variety_query:
            percentage = (variety_data.count / wine_count) * 100
            variety_info = VarietyInfo(
                name=variety_data.variety,
                count=variety_data.count,
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

    # Return the result
    return {"items": countries_data, "total_countries": len(countries_data)}
