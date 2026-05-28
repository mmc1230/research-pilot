from pathlib import Path

from fastapi import UploadFile

from app.services.document_service import save_upload
from app.storage import sqlite
from app.tools.csv_tools import analyze_metrics_csv, load_csv


def ingest_csv(file: UploadFile) -> dict:
    path = save_upload(file, "csv")
    schema = load_csv(str(path))
    analysis = analyze_metrics_csv(str(path))
    doc_id = sqlite.create_document(
        filename=Path(file.filename or path.name).name,
        file_path=path,
        doc_type="csv",
        collection_name=f"csv_{path.stem}",
        metadata={"rows": schema["rows"], "columns": schema["columns"]},
    )
    return {"document_id": doc_id, "schema": schema, "analysis": analysis}


def analyze_csv_by_id(document_id: int | str) -> dict:
    doc = sqlite.get_document(document_id)
    if not doc:
        raise KeyError(f"CSV document not found: {document_id}")
    return analyze_metrics_csv(doc["file_path"])
