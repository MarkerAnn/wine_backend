from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WineBase(BaseModel):
    title: str
    description: str
    points: int
    price: Optional[Decimal]
    country: Optional[str]
    province: Optional[str]
    region_1: Optional[str]
    region_2: Optional[str]
    designation: Optional[str]
    taster_name: Optional[str]
    taster_twitter_handle: Optional[str]
    variety: Optional[str]
    winery: Optional[str]


class Wine(WineBase):
    id: int
    created_at: Optional[datetime]
    source: Optional[str]

    # Config the model to work with ORM-objects
    model_config = ConfigDict(from_attributes=True)


class MyModel(BaseModel):
    model_config = {"from_attributes": True}


class WineList(BaseModel):
    items: List[Wine]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)


class WineSearch(BaseModel):
    search: Optional[str] = None  # the search frase from the user
    country: Optional[str] = None
    variety: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_points: Optional[int] = None
    max_points: Optional[int] = None
    page: int = 1
    size: int = 20

    model_config = ConfigDict(from_attributes=True)


class WineSearchResult(BaseModel):
    id: int
    title: str
    price: Optional[Decimal]
    points: int
    country: Optional[str]
    variety: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class WineSearchList(BaseModel):
    items: List[WineSearchResult]
    total: int
    page: int
    size: int
    pages: int

    model_config = ConfigDict(from_attributes=True)

