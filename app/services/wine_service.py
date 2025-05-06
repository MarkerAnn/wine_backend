import math
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
    """
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
            WineModel.search_vector.match(
                params.search, postgresql_regconfig="english"
            )
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
