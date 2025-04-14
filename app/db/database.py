from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# Create database engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    """
    Dependency function that yields a SQLAlchemy database session.
    This ensures the database session is closed after the request is complete.
    """
    db = SessionLocal()
    try:
        print("Connecting to DB:", DATABASE_URL)
        yield db
    finally:
        db.close()
