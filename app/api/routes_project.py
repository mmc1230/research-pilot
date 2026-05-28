from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.services.project_service import scan_and_index_project

router = APIRouter(prefix="/project", tags=["project"])


class ProjectScanRequest(BaseModel):
    project_path: str
    max_files: int = 80


@router.post("/scan")
def scan_project(request: ProjectScanRequest):
    try:
        return scan_and_index_project(request.project_path, max_files=request.max_files)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
