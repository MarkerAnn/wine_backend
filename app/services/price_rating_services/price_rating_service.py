from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.wine import Wine
from app.schemas.price_rating import PriceRatingResponse, PriceRatingDataPoint


# -------------------------
# Fetch raw wine datapoints
# -------------------------
def fetch_price_rating(
    db: Session,
    country: Optional[str],
    variety: Optional[str],
    min_price: Optional[float],
    max_price: Optional[float],
    min_points: Optional[int],
    max_points: Optional[int],
    page: int,
    page_size: int,
) -> PriceRatingResponse:
    """
    Fetch wine data filtered by price and rating.
    Each datapoint is used for a scatterplot (price vs rating).
    """
    # Start the query with required fields and only include rows where price and country exist
    query = db.query(
        Wine.id, Wine.price, Wine.points, Wine.country, Wine.variety, Wine.winery
    ).filter(Wine.price.isnot(None), Wine.country.isnot(None))

    # Apply filters if they are given, so we can use them in the query (e.g. country, variety)
    if country:
        query = query.filter(Wine.country == country)
    if variety:
        query = query.filter(Wine.variety == variety)
    if min_price is not None:
        query = query.filter(Wine.price >= min_price)
    if max_price is not None:
        query = query.filter(Wine.price <= max_price)
    if min_points is not None:
        query = query.filter(Wine.points >= min_points)
    if max_points is not None:
        query = query.filter(Wine.points <= max_points)

    # Count how many wines match before we limit it for pagination
    # This is important for the frontend to know how many pages there are
    total = query.count()

    # Apply pagination and fetch results
    wines = query.offset((page - 1) * page_size).limit(page_size).all()

    # Convert to Pydantic response model using correct Python types to match the pydantic schema
    data: List[PriceRatingDataPoint] = [
        PriceRatingDataPoint(
            id=wine.id,
            price=float(wine.price),
            points=int(wine.points),
            country=str(wine.country),
            variety=str(wine.variety),
            winery=str(wine.winery),
        )
        for wine in wines
    ]

    # Return the final response
    return PriceRatingResponse(data=data, total=total, page=page, page_size=page_size)
