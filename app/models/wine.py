# 🧠 Nya imports som krävs för korrekt typning
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Numeric, Text, DateTime, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.db.database import Base


class Wine(Base):
    """
    SQLAlchemy model for 'kaggle_wine_reviews' table.
    Declarative mixin wuith Mapped and mapped_column according to SQLAlchemy 2.0.
    """

    __tablename__ = "kaggle_wine_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    country: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    designation: Mapped[Optional[str]] = mapped_column(Text)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    province: Mapped[Optional[str]] = mapped_column(Text)
    region_1: Mapped[Optional[str]] = mapped_column(Text)
    region_2: Mapped[Optional[str]] = mapped_column(Text)
    taster_name: Mapped[Optional[str]] = mapped_column(Text)
    taster_twitter_handle: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    variety: Mapped[Optional[str]] = mapped_column(Text)
    winery: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[str]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    source: Mapped[Optional[str]] = mapped_column(Text, default="kaggle")
    search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR)
