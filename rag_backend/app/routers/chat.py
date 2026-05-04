from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/chat")

@router.post("/")
async def chat_endpoint(request: ChatRequest):
    rag = RAGService()
    context = ""  # TODO: replace with real retrieval result from rag.retrieve(request.question)
    answer = await rag.generate(context, request.question)
    return ChatResponse(answer=answer)
