"""
Handles Chroma vector store setup and operations.
"""

from typing import List, Dict, TypedDict, Any, TypeAlias
import chromadb
from app.core.config import VECTORSTORE_DIR

# Initialize Chroma client (persistent)
chroma_client = chromadb.PersistentClient(path=VECTORSTORE_DIR)

# Alias for Chroma collection type
ChromaCollection: TypeAlias = Any


class EmbeddingItem(TypedDict):
    """
    TypedDict to describe the structure of each embedding item.
    """

    id: int
    document: str
    embedding: List[float]
    metadata: Dict[str, str]


def get_or_create_collection(collection_name: str = "wine_reviews") -> ChromaCollection:
    """
    Get or create a Chroma collection.
    """
    return chroma_client.get_or_create_collection(name=collection_name)


def add_embeddings_to_chroma(
    collection: ChromaCollection,
    docs_with_embeddings: List[EmbeddingItem],
    batch_size: int = 1000,
) -> None:
    """
    Add documents with embeddings to Chroma collection in batches.
    :param collection: The Chroma collection.
    :param docs_with_embeddings: List of embedding items.
    :param batch_size: How many items to insert per batch.
    """
    total = len(docs_with_embeddings)
    print(f"ℹ️ Total items to add: {total}")

    for i in range(0, total, batch_size):
        batch = docs_with_embeddings[i : i + batch_size]

        ids = [str(item["id"]) for item in batch]
        documents = [item["document"] for item in batch]
        embeddings = [item["embedding"] for item in batch]
        metadatas = [item["metadata"] for item in batch]

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        print(f"✅ Added batch {i // batch_size + 1} ({len(batch)} items)")

