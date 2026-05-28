from pathlib import Path

from app.services.document_service import ingest_text_file
from app.rag.retriever import retrieve_chunks
from app.storage.sqlite import init_db


def test_text_rag_roundtrip(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    init_db()
    text_path = tmp_path / "note.txt"
    text_path.write_text("Graph neural networks are useful for molecular property prediction.", encoding="utf-8")

    result = ingest_text_file(str(text_path), doc_type="note")
    chunks = retrieve_chunks(result["collection_name"], "molecular property", k=1)
    assert chunks
    assert "molecular" in chunks[0]["content"].lower()
