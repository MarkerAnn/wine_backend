# app/db/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Modifiera engine med större pool och längre timeout
engine = create_engine(
    DATABASE_URL,
    pool_size=20,  # Decrease pool_size to 20
    max_overflow=20,  # Decrease max_overflow to 20
    pool_timeout=60,  # Longer timeout
    pool_pre_ping=True,  # Check if connection is alive before using it
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        print("Connection opened")
        yield db
    finally:
        # Se till att anslutningen stängs korrekt
        print("Connection closing")
        db.close()
