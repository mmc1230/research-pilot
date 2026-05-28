from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.document_service import ingest_document, ingest_paper
from app.services.experiment_service import ingest_csv

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/paper")
def upload_paper(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported for paper upload.")
    try:
        return ingest_paper(file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/document")
def upload_document(file: UploadFile = File(...)):
    try:
        return ingest_document(file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/csv")
def upload_csv(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    try:
        return ingest_csv(file)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
