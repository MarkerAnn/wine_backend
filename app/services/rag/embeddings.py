from typing import List, TypedDict
import numpy as np
from app.services.rag.vectorstore import chroma_client
from numpy.typing import NDArray
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
from app.models.wine import Wine
from app.core.config import EMBEDDING_MODEL_NAME
from app.services.rag.vectorstore import (
    get_or_create_collection,
    add_embeddings_to_chroma,
    EmbeddingItem,
)


class WineReview(TypedDict):
    """
    TypedDict for a wine review entry from the database.
    """

    id: int
    description: str
    title: str
    country: str
    variety: str


def get_all_reviews(session: Session) -> List[WineReview]:
    """
    Fetch all wine reviews from the database.
    :param session: SQLAlchemy session.
    :return: List of WineReview dicts.
    """
    reviews = session.query(
        Wine.id,
        Wine.description,
        Wine.title,
        Wine.country,
        Wine.variety,
    ).all()

    return [
        {
            "id": r.id,
            "description": r.description or "",
            "title": r.title or "",
            "country": r.country or "",
            "variety": r.variety or "",
        }
        for r in reviews
        if r.description
    ]


def process_and_store_embeddings(session: Session) -> None:
    """
    Process all wine reviews: create embeddings and store them in Chroma.
    :param session: SQLAlchemy session.
    """
    print("✅ Fetching reviews from DB...")
    reviews = get_all_reviews(session)
    print(f"➡️  {len(reviews)} reviews found.")

    if not reviews:
        print("⚠️ No reviews found. Exiting.")
        return

    texts = [review["description"] for review in reviews]

    print(f"🛠️  Loading embedding model: {EMBEDDING_MODEL_NAME}...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("🧠 Creating embeddings...")
    embeddings: NDArray[np.float32] = embedding_model.encode(
        texts, show_progress_bar=True, convert_to_numpy=True
    ) # type: ignore

    docs_with_embeddings: List[EmbeddingItem] = []
    for review, embedding in zip(reviews, embeddings):
        item: EmbeddingItem = {
            "id": review["id"],
            "document": review["description"],
            "embedding": embedding.tolist(),  # Chroma expects list[float]
            "metadata": {
                "id": str(review["id"]),
                "title": review["title"],
                "country": review["country"],
                "variety": review["variety"],
            },
        }
        docs_with_embeddings.append(item)

    print("🔗 Connecting to Chroma...")
    collection = get_or_create_collection()

    print(f"💾 Adding {len(docs_with_embeddings)} items to Chroma...")
    add_embeddings_to_chroma(collection, docs_with_embeddings)

    print("✅ All embeddings successfully stored in Chroma.")
