from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/chat")

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    rag = RAGService()
    retrieved = rag.retrieve(request.question, top_k=5)
    context = [r["content"] for r in retrieved]
    answer = await rag.generate(context, request.question)
    return ChatResponse(answer=answer)
