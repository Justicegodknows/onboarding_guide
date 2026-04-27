from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1/chat")

@router.post("/")
def chat_endpoint(request: ChatRequest):
    # Placeholder logic
    return ChatResponse(answer="This is a mock answer.")
