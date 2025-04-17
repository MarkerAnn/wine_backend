# country_stats.py (schema)
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel


class VarietyInfo(BaseModel):
    """
    Represents statistics about a grape variety in a country
    """

    name: str
    count: int
    percentage: float


class CountryStats(BaseModel):
    """
    Represents aggregated wine statistics for a country
    """

    country: str
    avg_points: float
    count: int
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    avg_price: Optional[float] = None
    top_varieties: List[VarietyInfo]


class CountriesStatsList(BaseModel):
    """
    A list of country statistics with metadata
    """

    items: List[CountryStats]
    total_countries: int
