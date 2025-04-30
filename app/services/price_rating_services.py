from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, cast, Integer, Numeric

from app.models.wine import Wine
from app.schemas.price_rating import PriceRatingResponse, PriceRatingDataPoint
from app.schemas.price_rating_aggregated import (
    AggregatedPriceRatingResponse,
    PriceRatingBucket,
    WineExample,
    HeatmapResponse,
    BucketExamplesResponse,
)










