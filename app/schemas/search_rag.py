from pydantic import BaseModel

class SearchRequest(BaseModel):
    query: str

class SearchResult(BaseModel):
    id: str
    title: str
    country: str
    variety: str
    description: str
