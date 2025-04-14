from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base


class Wine(Base):
    """
    SQLAlchemy model representing a wine in the database.
    Maps to the 'wines' table in PostgreSQL.
    """

    __tablename__ = "wines"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    capacity = Column(Numeric(10, 2))
    grape = Column(Text, nullable=False)
    secondary_grape_varieties = Column(Text)
    closure = Column(Text)
    country = Column(Text, nullable=False)
    unit = Column(Text)
    characteristics = Column(Text)
    per_unit = Column(Text)
    type = Column(Text, nullable=False)
    abv = Column(Numeric(5, 2), nullable=False)
    region = Column(Text)
    style = Column(Text, nullable=False)
    vintage = Column(Integer)
    appellation = Column(Text)
    currency = Column(Text, default="UNKNOWN")
    created_at = Column(DateTime(timezone=True), default=func.now())
    source = Column(Text, default="dataset")
