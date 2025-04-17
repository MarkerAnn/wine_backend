from typing import List
from pydantic import BaseModel


class PriceRatingDataPoint(BaseModel):
    """
    Represents a single wine data point for the price vs rating scatterplot.
    """

    id: int
    price: float
    points: int
    country: str
    variety: str
    winery: str


class PriceRatingResponse(BaseModel):
    """
    Response model for the price vs rating endpoint.
    """

    data: List[PriceRatingDataPoint]
    total: int
    page: int
    page_size: int
