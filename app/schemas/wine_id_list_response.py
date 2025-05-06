from typing import List, Optional
from pydantic import BaseModel

class Pagination(BaseModel):
    next_cursor: Optional[str]
    has_next: bool

class WineIdListResponse(BaseModel):
    country: str
    wine_ids: List[int]
    pagination: Pagination
