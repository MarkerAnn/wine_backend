from typing import List, Optional
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
    examples: List[WineExample] = Field(
        default_factory=list, description="Up to 3 example wines from this bucket"
    )


class AggregatedPriceRatingResponse(BaseModel):
    """
    Response model for aggregated price vs rating data
    """

    buckets: List[PriceRatingBucket]
    total_wines: int
    bucket_size: dict = Field(
        ..., description="Size of each bucket (e.g. {'price': 10, 'points': 1})"
    )


class HeatmapPoint(BaseModel):
    """Represents a single data point for the heatmap visualization"""

    x_index: int = Field(..., description="X-axis index (for price)")
    y_index: int = Field(..., description="Y-axis index (for rating)")
    value: int = Field(..., description="Count value for heatmap intensity")
    price_min: float = Field(..., description="Original price_min value")
    points_min: int = Field(..., description="Original points_min value")


class HeatmapResponse(BaseModel):
    """Response model for pre-formatted heatmap data"""

    data: List[List[int]] = Field(
        ..., description="Data points formatted for ECharts heatmap [x, y, value]"
    )
    x_categories: List[float] = Field(..., description="Price categories for x-axis")
    y_categories: List[int] = Field(..., description="Rating categories for y-axis")
    bucket_map: dict = Field(..., description="Lookup map for original bucket data")
    max_count: int = Field(..., description="Maximum count value for color scaling")
    total_wines: int = Field(..., description="Total number of wines in the selection")
    bucket_size: dict = Field(..., description="Size of each bucket")
