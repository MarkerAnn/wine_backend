# app/schemas/bucket_wines.py
from typing import List, Optional
from pydantic import BaseModel, Field


class WineInBucket(BaseModel):
    """
    Represents a wine in a specific price-rating bucket
    """

    id: int = Field(..., description="Wine ID")
    name: str = Field(..., description="Name of the wine (from title)")
    winery: str = Field(..., description="Winery name")
    price: float = Field(..., description="Price of the wine in USD")
    points: int = Field(..., description="Rating points (80-100)")
    country: Optional[str] = Field(None, description="Country of origin")
    variety: Optional[str] = Field(None, description="Wine variety/grape")


class BucketWinesPagination(BaseModel):
    """
    Pagination information for bucket wines endpoint
    """

    next_cursor: Optional[str] = Field(None, description="Cursor for the next page")
    has_next: bool = Field(..., description="Whether there are more results")


class BucketWinesResponse(BaseModel):
    """
    Response model for wines in a bucket endpoint
    """

    wines: List[WineInBucket] = Field(..., description="List of wines in the bucket")
    pagination: BucketWinesPagination = Field(..., description="Pagination information")
    total: int = Field(..., description="Total number of wines in this bucket")
