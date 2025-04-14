from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import math

from app.db.database import get_db
from app.models.wine import Wine
from app.schemas.wine import Wine as WineSchema, WineList

router = APIRouter()

@router.get("/{wine_id}", response_model=WineSchema)
def get_wine(wine_id: int, db: Session = Depends(get_db)):
    """
    Get a specific wine by ID
    
    Parameters:
    - wine_id: The ID of the wine to retrieve
    
    Returns:
    - Wine: The wine object if found
    
    Raises:
    - HTTPException: If wine not found
    """
    wine = db.query(Wine).filter(Wine.id == wine_id).first()
    if wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return wine

@router.get("/", response_model=WineList)
def get_wines(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size")
):
    """
    Get a paginated list of wines
    
    Parameters:
    - page: The page number (starts at 1)
    - size: Number of items per page
    
    Returns:
    - WineList: Paginated list of wines
    """
    # Calculate offset
    skip = (page - 1) * size
    
    # Get total count
    total = db.query(Wine).count()
    
    # Get wines for current page
    wines = db.query(Wine).offset(skip).limit(size).all()
    
    # Calculate total pages
    pages = math.ceil(total / size)
    
    return {
        "items": wines,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }