from fastapi import APIRouter

from app.models.schemas import TrainerRequest, TrainerResponse
from app.services.trainer_agent import TrainerSubAgent

router = APIRouter(prefix="/api/v1/trainer", tags=["trainer"])


@router.post("/", response_model=TrainerResponse)
async def trainer_endpoint(request: TrainerRequest):
    agent = TrainerSubAgent()
    answer = await agent.answer(
        question=request.question,
        history=request.history,
    )
    return TrainerResponse(answer=answer)
