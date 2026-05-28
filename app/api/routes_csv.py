from fastapi import APIRouter, HTTPException

from app.services.experiment_service import analyze_csv_by_id

router = APIRouter(prefix="/csv", tags=["csv"])


@router.get("/{document_id}/analysis")
def csv_analysis(document_id: int):
    try:
        return analyze_csv_by_id(document_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
