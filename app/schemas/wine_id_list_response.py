from typing import List, Optional
from pydantic import BaseModel
from app.schemas.wine import WineSearchResult


class WineListByCountryResponse(BaseModel):
    country: str
    wines: List[WineSearchResult]
    next_cursor: Optional[str]
    has_next: bool
