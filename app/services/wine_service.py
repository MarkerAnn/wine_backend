import math
import base64
import json
import binascii

from typing import Optional

from sqlalchemy.orm import Session

from app.models.wine import Wine as WineModel
from app.schemas.wine import (
    Wine as WineSchema,
    WineList,
    WineSearch,
    WineSearchResult,
    WineSearchList,
)
from app.schemas.wine_id_list_response import WineListByCountryResponse


def get_wine_by_id(db: Session, wine_id: int) -> Optional[WineModel]:
    """
    Retrieve a single WineModel by its ID.
    Returns None if not found.
    """
    return db.query(WineModel).filter(WineModel.id == wine_id).first()


def get_wines_paginated(db: Session, page: int, size: int) -> WineList:
    """
    Retrieve paginated list of all wines.
    """
    if page < 1:
        raise ValueError("Page number must be at least 1")
    if size < 1:
        raise ValueError("Page size must be at least 1")

    skip = (page - 1) * size
    total = db.query(WineModel).count()
    wines = db.query(WineModel).offset(skip).limit(size).all()
    wine_schemas = [WineSchema.model_validate(w) for w in wines]
    pages = math.ceil(total / size)
    return WineList(
        items=wine_schemas,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def search_wines(db: Session, params: WineSearch) -> WineSearchList:
    """
    Search and filter wines based on criteria in WineSearch.
    Raises ValueError for invalid parameter combinations.
    """
    # Validate pagination
    if params.page < 1:
        raise ValueError("Page number must be at least 1")
    if params.size < 1:
        raise ValueError("Page size must be at least 1")

    # Validate price range
    if (
        params.min_price is not None
        and params.max_price is not None
        and params.min_price > params.max_price
    ):
        raise ValueError(
            f"Invalid price range: min_price={params.min_price}, max_price={params.max_price}"
        )

    # Validate points range
    if (
        params.min_points is not None
        and params.max_points is not None
        and params.min_points > params.max_points
    ):
        raise ValueError(
            f"Invalid points range: min_points={params.min_points}, max_points={params.max_points}"
        )

    # Start building the query
    query = db.query(
        WineModel.id,
        WineModel.title,
        WineModel.price,
        WineModel.points,
        WineModel.country,
        WineModel.variety,
    )

    if params.search:
        query = query.filter(
            WineModel.search_vector.match(params.search, postgresql_regconfig="english")
        )
    if params.country:
        query = query.filter(WineModel.country == params.country)
    if params.variety:
        query = query.filter(WineModel.variety == params.variety)
    if params.min_price is not None:
        query = query.filter(WineModel.price >= params.min_price)
    if params.max_price is not None:
        query = query.filter(WineModel.price <= params.max_price)
    if params.min_points is not None:
        query = query.filter(WineModel.points >= params.min_points)
    if params.max_points is not None:
        query = query.filter(WineModel.points <= params.max_points)

    total = query.count()
    skip = (params.page - 1) * params.size
    wines = query.offset(skip).limit(params.size).all()

    results = [
        WineSearchResult(
            id=w.id,
            title=w.title,
            price=w.price,
            points=w.points,
            country=w.country,
            variety=w.variety,
        )
        for w in wines
    ]
    pages = math.ceil(total / params.size)

    return WineSearchList(
        items=results,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


def get_wine_details_by_country(
    db: Session,
    country: str,
    limit: int = 100,
    cursor: Optional[str] = None,
) -> WineListByCountryResponse:
    """
    Fetch paginated wine details for a specific country.
    """
    query = db.query(
        WineModel.id,
        WineModel.title,
        WineModel.price,
        WineModel.points,
        WineModel.country,
        WineModel.variety,
        WineModel.winery,
    ).filter(WineModel.country == country)

    if cursor:
        try:
            decoded = base64.b64decode(cursor).decode("utf-8")
            cursor_data = json.loads(decoded)
            last_id = cursor_data.get("last_id")
            if last_id:
                query = query.filter(WineModel.id > last_id)
        except (json.JSONDecodeError, ValueError, binascii.Error) as e:
            raise ValueError("Invalid cursor format") from e

    query = query.order_by(WineModel.id).limit(limit + 1)
    results = query.all()

    wines = [
        WineSearchResult(
            id=w.id,
            title=w.title,
            price=w.price,
            points=w.points,
            country=w.country,
            variety=w.variety,
        )
        for w in results[:limit]
    ]

    has_next = len(results) > limit
    next_cursor = None

    if has_next and wines:
        cursor_data = {"last_id": wines[-1].id}
        next_cursor = base64.b64encode(json.dumps(cursor_data).encode("utf-8")).decode(
            "utf-8"
        )

    return WineListByCountryResponse(
        country=country,
        wines=wines,
        next_cursor=next_cursor,
        has_next=has_next,
    )
