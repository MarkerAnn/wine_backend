from typing import List, Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.retrieval_qa.base import RetrievalQA 
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

def answer_with_rag(query: str) -> Tuple[str, List[str]]:
    """
    Use RAG to answer a query, strictly using only the Chroma data.
    """
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)

    prompt = ChatPromptTemplate.from_template(
        """
        You are a wine expert. Answer the user's question based only on the provided wine reviews.

        **First, provide a recommendation and motivation in your own words.**

        **Then, list the descriptions of the most relevant wines retrieved from the database, formatted as follows:**

        Recommended Wine Descriptions:
        {context}

        User Question: {question}
        """
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )

    result = qa_chain.invoke({"query": query})

    answer = result["result"]
    sources = [doc.page_content for doc in result.get("source_documents", [])]

    # Print the generated answer
    print("\n=== Generated Answer ===")
    print(answer)

    # Print the retrieved source documents
    print("\n=== Retrieved Documents ===")
    if sources:
        for i, source in enumerate(sources, start=1):
            print(f"\n--- Source Document {i} ---\n{source}")
    else:
        print("No source documents were retrieved.")

    return answer, sources

