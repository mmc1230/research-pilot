from app.rag.retriever import retrieve_chunks
from app.storage.sqlite import get_document
from app.tools.tool_registry import register_tool


@register_tool(
    name="search_vector_store",
    description="Search a named vector collection and return relevant chunks.",
    args_schema={"query": "string", "collection_name": "string", "k": "integer"},
)
def search_vector_store(query: str, collection_name: str, k: int = 5) -> dict:
    return {"query": query, "collection_name": collection_name, "chunks": retrieve_chunks(collection_name, query, k)}


@register_tool(
    name="get_document_metadata",
    description="Return saved metadata for an uploaded document.",
    args_schema={"document_id": "integer"},
)
def get_document_metadata(document_id: int | str) -> dict:
    doc = get_document(document_id)
    if not doc:
        raise KeyError(f"Document not found: {document_id}")
    return doc
