# app/services/country_stats_service.py

from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.wine import Wine
from app.schemas.country_stats import CountryStats, CountriesStatsList, VarietyInfo
from app.utils.country_mapping import get_geojson_country_name

# -------------------------
# Service to fetch country-level wine statistics
# -------------------------
def fetch_country_stats(db: Session, min_wines: int = 50) -> CountriesStatsList:
    """
    Fetch country-level wine statistics including top varieties.
    This is used to generate the country overview.
    """
    # First query: basic statistics per country
    country_stats_query = (
        db.query(
            Wine.country,
            func.avg(Wine.points).label(
                "avg_points"
            ),  # Func is imported from sqlalchemy
            func.count(Wine.id).label("count"),
            func.min(Wine.price).label("min_price"),
            func.max(Wine.price).label("max_price"),
            func.avg(Wine.price).label("avg_price"),
        )
        .filter(Wine.country.isnot(None))
        .group_by(Wine.country)
        .having(func.count(Wine.id) >= min_wines)
        .order_by(func.count(Wine.id).desc())
        .all()
    )

    countries_data: List[CountryStats] = []

    for country_data in country_stats_query:
        country_name = country_data.country
        wine_count = int(getattr(country_data, "count"))
        geojson_country_name = get_geojson_country_name(country_name)  # Convert to geojson name, to match the map in the frontend

        # Second query: top varieties(druvsort) for the country
        variety_query = (
            db.query(Wine.variety, func.count(Wine.id).label("count"))
            .filter(Wine.country == country_name, Wine.variety.isnot(None))
            .group_by(Wine.variety)
            .order_by(func.count(Wine.id).desc())
            .limit(5)
            .all()
        )

        top_varieties: List[VarietyInfo] = []

        # calcultate percentage of each variety (druvsorten)
        # Add to the list of top varieties
        for variety_data in variety_query:
            variety_count = int(getattr(variety_data, "count"))
            percentage = (variety_count / wine_count) * 100
            top_varieties.append(
                VarietyInfo(
                    name=variety_data.variety,
                    count=variety_count,
                    percentage=round(percentage, 2),
        )
    )

        # Create a CountryStats object and append to the list
        # round the avg_points and avg_price to 2 decimal places
        countries_data.append(
            CountryStats(
                country=geojson_country_name,
                original_country=country_name,
                avg_points=round(float(country_data.avg_points), 2),
                count=wine_count,
                min_price=country_data.min_price,
                max_price=country_data.max_price,
                avg_price=(
                    round(float(country_data.avg_price), 2)
                    if country_data.avg_price is not None
                    else None
                ),
                top_varieties=top_varieties,
            )
        )

    return CountriesStatsList(items=countries_data, total_countries=len(countries_data))
