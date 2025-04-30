from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.price_rating import PriceRatingResponse
from app.schemas.price_rating_aggregated import (
    AggregatedPriceRatingResponse,
    HeatmapResponse,
    BucketExamplesResponse,
)
from app.services.price_rating_services import (
    fetch_price_rating,
    fetch_aggregated_price_rating,
    fetch_price_rating_heatmap,
    fetch_bucket_examples,
)

router = APIRouter(
    prefix="/api/stats",
    tags=["price-rating"],
)


@router.get(
    "/price-rating",
    response_model=PriceRatingResponse,
    summary="Fetch individual wine price vs. rating data",
)
def get_price_rating(
    *,
    country: Optional[str] = Query(None, description="Country filter"),
    variety: Optional[str] = Query(None, description="Variety filter"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_points: Optional[int] = Query(None, ge=0, description="Minimum points"),
    max_points: Optional[int] = Query(None, ge=0, description="Maximum points"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(1000, ge=1, description="Items per page"),
    db: Session = Depends(get_db),
) -> PriceRatingResponse:
    """
    Endpoint returning raw wine price/rating datapoints with pagination.
    """
    return fetch_price_rating(
        db=db,
        country=country,
        variety=variety,
        min_price=min_price,
        max_price=max_price,
        min_points=min_points,
        max_points=max_points,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/price-rating-aggregated",
    response_model=AggregatedPriceRatingResponse,
    summary="Fetch aggregated price/rating buckets",
)
def get_aggregated_price_rating(
    *,
    price_bucket_size: float = Query(10.0, gt=0, description="Price bucket size"),
    points_bucket_size: int = Query(1, gt=0, description="Points bucket size"),
    country: Optional[str] = Query(None),
    variety: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_points: Optional[int] = Query(None, ge=0),
    max_points: Optional[int] = Query(None, ge=0),
    page: Optional[int] = Query(None, ge=1, description="Page number"),
    page_size: Optional[int] = Query(
        None, ge=1, le=500, description="Buckets per page"
    ),
    db: Session = Depends(get_db),
) -> AggregatedPriceRatingResponse:
    """
    Endpoint returning bucketed counts and examples for wine price vs rating.
    """
    return fetch_aggregated_price_rating(
        db=db,
        price_bucket_size=price_bucket_size,
        points_bucket_size=points_bucket_size,
        country=country,
        variety=variety,
        min_price=min_price,
        max_price=max_price,
        min_points=min_points,
        max_points=max_points,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/price-rating-heatmap",
    response_model=HeatmapResponse,
    summary="Fetch heatmap data for price vs rating distribution",
)
def get_price_rating_heatmap(
    *,
    price_bucket_size: float = Query(10.0, gt=0),
    points_bucket_size: int = Query(1, gt=0),
    country: Optional[str] = Query(None),
    variety: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_points: Optional[int] = Query(None, ge=0),
    max_points: Optional[int] = Query(None, ge=0),
    db: Session = Depends(get_db),
) -> HeatmapResponse:
    """
    Endpoint returning pre-formatted heatmap arrays and metadata for frontend.
    """
    return fetch_price_rating_heatmap(
        db=db,
        price_bucket_size=price_bucket_size,
        points_bucket_size=points_bucket_size,
        country=country,
        variety=variety,
        min_price=min_price,
        max_price=max_price,
        min_points=min_points,
        max_points=max_points,
    )


@router.get(
    "/bucket-examples/{price_min}/{points_min}",
    response_model=BucketExamplesResponse,
    summary="Fetch example wines from a specific bucket",
)
def get_bucket_examples(
    price_min: float,
    points_min: int,
    price_bucket_size: float = Query(10.0, gt=0),
    points_bucket_size: int = Query(1, gt=0),
    country: Optional[str] = Query(None),
    variety: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> BucketExamplesResponse:
    """
    Endpoint returning example wines from a specific price/rating bucket.
    """
    return fetch_bucket_examples(
        db=db,
        price_min=price_min,
        points_min=points_min,
        price_bucket_size=price_bucket_size,
        points_bucket_size=points_bucket_size,
        country=country,
        variety=variety,
    )
