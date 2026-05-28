from pathlib import Path
from uuid import uuid4

from langchain_core.documents import Document

from app.rag.splitter import split_documents
from app.rag.vector_store import add_documents
from app.storage import sqlite
from app.tools.code_tools import scan_project_tree, summarize_code_file


def scan_and_index_project(project_path: str, max_files: int = 80) -> dict:
    scan = scan_project_tree(project_path)
    files = scan["source_files"][:max_files]
    summaries = []
    docs = []
    for file_path in files:
        try:
            summary = summarize_code_file(file_path)
        except Exception as exc:
            summary = {"file_path": file_path, "error": str(exc)}
        summaries.append(summary)
        if "preview" in summary:
            content = (
                f"File: {summary['file_path']}\n"
                f"Classes: {summary.get('classes', [])}\n"
                f"Functions: {summary.get('functions', [])}\n\n"
                f"{summary['preview']}"
            )
            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": summary["file_path"],
                        "filename": Path(summary["file_path"]).name,
                        "doc_type": "code",
                    },
                )
            )

    collection_name = f"project_{uuid4().hex}"
    doc_id = sqlite.create_document(
        filename=Path(project_path).resolve().name,
        file_path=str(Path(project_path).resolve()),
        doc_type="project",
        collection_name=collection_name,
        metadata={"file_count": scan["file_count"]},
    )
    chunks = split_documents(docs, chunk_size=1200, chunk_overlap=120) if docs else []
    ids = [f"project-{doc_id}-chunk-{i}" for i in range(len(chunks))]
    for idx, chunk in enumerate(chunks):
        chunk.metadata.update({"document_id": doc_id, "chunk_index": idx})
    if chunks:
        add_documents(collection_name, chunks, ids)
    for idx, chunk_id in enumerate(ids):
        sqlite.add_chunk_metadata(doc_id, idx, chunk_id, None, chunks[idx].metadata.get("source", project_path))
    sqlite.update_document_chunk_count(doc_id, len(chunks))

    architecture_summary = {
        "project_id": doc_id,
        "collection_name": collection_name,
        "tree": scan["tree"],
        "file_count": scan["file_count"],
        "indexed_files": len(files),
        "summaries": summaries[:30],
    }
    return architecture_summary
