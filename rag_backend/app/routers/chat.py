from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/chat")

@router.post("/")
def chat_endpoint(request: ChatRequest):
    rag = RAGService()
    # For now, context is empty or could be improved with retrieval logic
    context = ""
    answer = rag.generate(context, request.question)
    return ChatResponse(answer=answer)
