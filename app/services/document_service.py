import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import get_settings
from app.rag.loaders import load_pdf, load_text
from app.rag.splitter import split_documents
from app.rag.vector_store import add_documents
from app.storage import sqlite


def save_upload(file: UploadFile, subdir: str) -> Path:
    settings = get_settings()
    target_dir = settings.upload_dir / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or f"upload-{uuid4()}").name
    target_path = target_dir / f"{uuid4().hex}-{safe_name}"
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return target_path


def ingest_paper(file: UploadFile) -> dict:
    path = save_upload(file, "papers")
    docs = load_pdf(path)
    chunks = split_documents(docs)
    collection_name = f"paper_{uuid4().hex}"
    document_id = sqlite.create_document(
        filename=Path(file.filename or path.name).name,
        file_path=path,
        doc_type="paper",
        collection_name=collection_name,
        metadata={"pages": len(docs)},
    )
    ids = [f"doc-{document_id}-chunk-{i}" for i in range(len(chunks))]
    for idx, chunk in enumerate(chunks):
        chunk.metadata.update({"document_id": document_id, "chunk_index": idx})
    add_documents(collection_name, chunks, ids)
    for idx, chunk_id in enumerate(ids):
        sqlite.add_chunk_metadata(
            document_id=document_id,
            chunk_index=idx,
            vector_id=chunk_id,
            section=chunks[idx].metadata.get("section"),
            source=chunks[idx].metadata.get("source", str(path)),
        )
    sqlite.update_document_chunk_count(document_id, len(chunks))
    return {
        "document_id": document_id,
        "filename": Path(file.filename or path.name).name,
        "collection_name": collection_name,
        "chunk_count": len(chunks),
    }


def ingest_document(file: UploadFile) -> dict:
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return ingest_paper(file)
    supported_text = {
        ".md",
        ".txt",
        ".py",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".yaml",
        ".yml",
        ".json",
        ".toml",
    }
    if suffix not in supported_text:
        raise ValueError(f"Unsupported document type: {suffix}")

    path = save_upload(file, "documents")
    doc_type = "code" if suffix in {".py", ".cpp", ".c", ".h", ".hpp"} else "text"
    docs = load_text(path, doc_type=doc_type)
    chunks = split_documents(docs)
    collection_name = f"{doc_type}_{uuid4().hex}"
    document_id = sqlite.create_document(
        filename=filename or path.name,
        file_path=path,
        doc_type=doc_type,
        collection_name=collection_name,
    )
    ids = [f"doc-{document_id}-chunk-{i}" for i in range(len(chunks))]
    for idx, chunk in enumerate(chunks):
        chunk.metadata.update({"document_id": document_id, "chunk_index": idx})
    add_documents(collection_name, chunks, ids)
    for idx, chunk_id in enumerate(ids):
        sqlite.add_chunk_metadata(document_id, idx, chunk_id, chunks[idx].metadata.get("section"), str(path))
    sqlite.update_document_chunk_count(document_id, len(chunks))
    return {
        "document_id": document_id,
        "filename": filename or path.name,
        "doc_type": doc_type,
        "collection_name": collection_name,
        "chunk_count": len(chunks),
    }


def ingest_text_file(path: str, doc_type: str = "text") -> dict:
    docs = load_text(path, doc_type=doc_type)
    chunks = split_documents(docs)
    collection_name = f"{doc_type}_{uuid4().hex}"
    document_id = sqlite.create_document(
        filename=Path(path).name,
        file_path=path,
        doc_type=doc_type,
        collection_name=collection_name,
    )
    ids = [f"doc-{document_id}-chunk-{i}" for i in range(len(chunks))]
    for idx, chunk in enumerate(chunks):
        chunk.metadata.update({"document_id": document_id, "chunk_index": idx})
    add_documents(collection_name, chunks, ids)
    for idx, chunk_id in enumerate(ids):
        sqlite.add_chunk_metadata(document_id, idx, chunk_id, chunks[idx].metadata.get("section"), path)
    sqlite.update_document_chunk_count(document_id, len(chunks))
    return {"document_id": document_id, "collection_name": collection_name, "chunk_count": len(chunks)}


def list_documents() -> list[dict]:
    return sqlite.list_documents()
