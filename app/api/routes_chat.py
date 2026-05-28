from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.services.chat_service import run_chat

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    source_type: str
    source_id: str | None = None
    session_id: str | None = None


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        return run_chat(
            question=request.question,
            source_type=request.source_type,
            source_id=request.source_id,
            session_id=request.session_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
