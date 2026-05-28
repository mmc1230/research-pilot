from app.rag.vector_store import similarity_search


def retrieve_chunks(collection_name: str, query: str, k: int = 5) -> list[dict]:
    docs = similarity_search(collection_name, query, k=k)
    results = []
    for doc in docs:
        results.append(
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source"),
                "page": doc.metadata.get("page"),
                "section": doc.metadata.get("section"),
            }
        )
    return results
