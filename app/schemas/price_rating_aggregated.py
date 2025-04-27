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


class VarietyCount(BaseModel):
    """
    Represents a variety and its count in a bucket
    """

    variety: str = Field(..., description="Variety/grape name")
    count: int = Field(..., description="Number of wines of this variety")


class BucketMapItem(BaseModel):
    """
    Detailed information about a specific price-point bucket for hover display
    """

    price_min: float = Field(..., description="Lower bound of price range")
    price_max: float = Field(..., description="Upper bound of price range")
    points_min: int = Field(..., description="Lower bound of rating range")
    points_max: int = Field(..., description="Upper bound of rating range")
    count: int = Field(..., description="Number of wines in this bucket")
    avg_price: float = Field(..., description="Average price of wines in this bucket")
    price_range: str = Field(..., description="Human-readable price range")
    top_varieties: List[VarietyCount] = Field(
        ..., description="Most common varieties in this bucket"
    )
    examples: List[WineExample] = Field(
        default_factory=list, description="Example wines from this bucket"
    )


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
    bucket_size: Dict[str, Union[float, int]] = Field(
        ..., description="Size of each bucket (e.g. {'price': 10, 'points': 1})"
    )


class HeatmapResponse(BaseModel):
    """Response model for pre-formatted heatmap data"""

    data: List[List[int]] = Field(
        ..., description="Data points formatted for ECharts heatmap [x, y, value]"
    )
    x_categories: List[float] = Field(..., description="Price categories for x-axis")
    y_categories: List[int] = Field(..., description="Rating categories for y-axis")
    bucket_map: Dict[str, BucketMapItem] = Field(
        ...,
        description="Lookup map for hover info with key format 'price_min-points_min'",
    )
    max_count: int = Field(..., description="Maximum count value for color scaling")
    total_wines: int = Field(..., description="Total number of wines in the selection")
    bucket_size: Dict[str, Union[float, int]] = Field(
        ..., description="Size of each bucket"
    )
