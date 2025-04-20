from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


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


class MyModel(BaseModel):
    model_config = {"from_attributes": True}


class WineList(BaseModel):
    items: List[Wine]
    total: int
    page: int
    size: int
    pages: int
