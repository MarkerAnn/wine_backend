from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.search_rag import SearchRequest, SearchResult
from app.services.rag.rag_chain import search_wines, answer_with_rag

router = APIRouter(
    prefix="/api/search",
    tags=["search_rag"],
)


@router.post("/", response_model=List[SearchResult])
async def search_endpoint(request: SearchRequest):
    """
    Search for wine reviews based on an English query.
    """
    results = search_wines(request.query)
    if not results:
        raise HTTPException(status_code=404, detail="No results found.")
    return results

@router.post("/answer")
async def answer_endpoint(request: SearchRequest):
    """
    Answer a wine-related question using RAG (retrieval + generation).
    """
    result = answer_with_rag(request.query)
    return result
