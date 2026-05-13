from fastapi import APIRouter

from app.models.schemas import TrainerRequest, TrainerResponse
from app.services.rag_chain import retrieve_context
from app.services.rag_service import RAGService

router = APIRouter(prefix="/api/v1/trainer", tags=["trainer"])


TRAINER_SYSTEM_PROMPT = (
    "You are Trainer, focused on employee onboarding and enablement. "
    "Answer strictly from the provided retrieved context. "
    "If evidence is missing in context, say so explicitly and avoid guessing."
)


@router.post("/", response_model=TrainerResponse)
async def trainer_endpoint(request: TrainerRequest):
    question = request.question.strip()
    context = await retrieve_context(question, top_k=6)
    rag = RAGService()
    answer = await rag.generate(
        context=context,
        question=question,
        system_prompt=TRAINER_SYSTEM_PROMPT,
    )
    return TrainerResponse(answer=answer)
