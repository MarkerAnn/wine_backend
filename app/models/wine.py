from sqlalchemy import Column, Integer, Numeric, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import TSVECTOR
from app.db.database import Base


class Wine(Base):
    """
    SQLAlchemy model for 'kaggle_wine_reviews' table.
    """

    __tablename__ = "kaggle_wine_reviews"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(Text)
    description = Column(Text, nullable=False)
    designation = Column(Text)
    points = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2))
    province = Column(Text)
    region_1 = Column(Text)
    region_2 = Column(Text)
    taster_name = Column(Text)
    taster_twitter_handle = Column(Text)
    title = Column(Text, nullable=False)
    variety = Column(Text)
    winery = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())  # noqa: E1102
    source = Column(Text, default="kaggle")
    search_vector = Column(TSVECTOR)
