"""
Script to create embeddings for all wine reviews and store them in Chroma.
"""

from sqlalchemy.orm import sessionmaker
from app.db.database import engine
from app.services.rag.embeddings import process_and_store_embeddings

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def main() -> None:
    """
    Main function to run the embedding process.
    """
    print("🚀 Starting the embedding pipeline...")
    with SessionLocal() as session:
        process_and_store_embeddings(session)
    print("✅ Embedding pipeline finished successfully.")

if __name__ == "__main__":
    main()
