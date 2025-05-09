from typing import Dict, Union, List
from pydantic import BaseModel, Field


class WineExample(BaseModel):
    """
    Represents a sample wine from a bucket for tooltip display
    """

    name: str = Field(..., description="Name of the wine")
    price: float = Field(..., description="Price of the wine in USD")
    points: int = Field(..., description="Rating points (80-100)")
    winery: str = Field(..., description="Winery name")


class PriceRatingBucket(BaseModel):
    """
    Represents an aggregated group of wines within a specific price and rating range
    """

    price_min: float = Field(..., description="Lower bound of price range")
    price_max: float = Field(..., description="Upper bound of price range")
    points_min: int = Field(..., description="Lower bound of rating range")
    points_max: int = Field(..., description="Upper bound of rating range")
    count: int = Field(..., description="Number of wines in this bucket")


class AggregatedPriceRatingResponse(BaseModel):
    """
    Response model for aggregated price vs rating data
    """

    buckets: List[PriceRatingBucket]
    total_wines: int
    total_buckets: int
    bucket_size: Dict[str, Union[float, int]] = Field(
        ..., description="Size of each bucket (e.g. {'price': 10, 'points': 1})"
    )
