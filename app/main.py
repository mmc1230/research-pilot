from fastapi import FastAPI, HTTPException

from app.api.routes_chat import router as chat_router
from app.api.routes_csv import router as csv_router
from app.api.routes_project import router as project_router
from app.api.routes_upload import router as upload_router
from app.services.document_service import list_documents
from app.storage.sqlite import get_logs, init_db

app = FastAPI(title="ResearchPilot", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": "ResearchPilot"}


@app.get("/documents")
def documents() -> list[dict]:
    return list_documents()


@app.get("/logs/{session_id}")
def logs(session_id: str) -> dict:
    try:
        return get_logs(session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


app.include_router(upload_router)
app.include_router(project_router)
app.include_router(csv_router)
app.include_router(chat_router)
