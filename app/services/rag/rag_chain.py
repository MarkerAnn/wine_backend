from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.core.config import VECTORSTORE_DIR, EMBEDDING_MODEL_NAME
from app.schemas.search_rag import SearchResult

embedding_function = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)

vectorstore = Chroma(
    collection_name="wine_reviews",
    embedding_function=embedding_function,
    persist_directory=VECTORSTORE_DIR,
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

def search_wines(query: str) -> List[SearchResult]:
    """
    Search for relevant wine reviews based on a text query.
    :param query: User's text query in English.
    :return: List of search results.
    """
    docs = retriever.get_relevant_documents(query)

    results: List[SearchResult] = []
    for doc in docs:
        metadata: Dict[str, Any] = doc.metadata
        results.append(
            SearchResult(
                id=metadata.get("id", ""),
                title=metadata.get("title", ""),
                country=metadata.get("country", ""),
                variety=metadata.get("variety", ""),
                description=doc.page_content,
            )
        )
    return results
