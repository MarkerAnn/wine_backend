from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.country_stats import CountriesStatsList
from app.services.country_stats_service import fetch_country_stats

router = APIRouter(
    prefix="/stats",
    tags=["country-stats"],
)


@router.get("/countries", response_model=CountriesStatsList)
def get_countries_stats(
    db: Session = Depends(get_db),
    min_wines: int = Query(
        50, description="Minimum number of wines to include a country"
    ),
) -> CountriesStatsList:
    """
    Get country-level wine statistics including average scores, prices and top varieties.
    """
    return fetch_country_stats(db=db, min_wines=min_wines)
