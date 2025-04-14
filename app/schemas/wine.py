from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class WineBase(BaseModel):
    """Base schema with common wine attributes"""
    title: str
    description: str
    price: Decimal
    country: str
    type: str
    abv: Decimal
    style: str

class Wine(WineBase):
    """Complete wine schema with all attributes"""
    id: int
    capacity: Optional[Decimal] = None
    grape: str
    secondary_grape_varieties: Optional[str] = None
    closure: Optional[str] = None
    unit: Optional[Decimal] = None
    characteristics: Optional[str] = None
    per_unit: Optional[str] = None
    region: Optional[str] = None
    vintage: Optional[int] = None
    appellation: Optional[str] = None
    currency: str

    class Config:
        """Configure Pydantic to handle SQLAlchemy models"""
        orm_mode = True

class WineList(BaseModel):
    """Schema for a paginated list of wines"""
    items: List[Wine]
    total: int
    page: int
    size: int
    pages: int