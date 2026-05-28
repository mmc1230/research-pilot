from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import get_settings
from app.rag.embeddings import get_embeddings


def get_collection(collection_name: str) -> Chroma:
    settings = get_settings()
    persist_dir = Path(settings.vector_db_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )


def add_documents(collection_name: str, documents: list[Document], ids: list[str]) -> None:
    store = get_collection(collection_name)
    store.add_documents(documents, ids=ids)


def similarity_search(collection_name: str, query: str, k: int = 5) -> list[Document]:
    store = get_collection(collection_name)
    return store.similarity_search(query, k=k)
