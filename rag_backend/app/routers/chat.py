from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/chat")

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    rag = RAGService()
    context = ""  # TODO: replace with real retrieval result from rag.retrieve(request.question)
    try:
        answer = await rag.generate(context, request.question)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LM Studio error: {e}")
    return ChatResponse(answer=answer)
