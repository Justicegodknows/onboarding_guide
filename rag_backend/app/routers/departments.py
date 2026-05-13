from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ChatResponse,
    DepartmentChatRequest,
    DepartmentInfo,
    TrainerResponse,
)
from app.services.departments_service import DEPARTMENTS, get_department
from app.services.rag_chain import retrieve_context
from app.services.rag_service import RAGService


router = APIRouter(prefix="/api/v1/departments", tags=["departments"])


def _grounded_system_prompt(base_prompt: str) -> str:
    return (
        f"{(base_prompt or '').strip()}\n\n"
        "Grounding rules:\n"
        "- Answer strictly from the provided context chunks.\n"
        "- If the context does not contain enough evidence, say so clearly.\n"
        "- Do not use external knowledge."
    )


@router.get("/", response_model=List[DepartmentInfo])
def list_departments() -> List[DepartmentInfo]:
    return DEPARTMENTS


@router.get("/{department_id}", response_model=DepartmentInfo)
def get_department_details(department_id: str) -> DepartmentInfo:
    department = get_department(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.post("/{department_id}/chat", response_model=ChatResponse)
async def department_chat(department_id: str, request: DepartmentChatRequest) -> ChatResponse:
    department = get_department(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    question = f"[{department.name}] {request.question.strip()}"
    context = await retrieve_context(question, top_k=6)

    rag = RAGService()
    answer = await rag.generate(
        context,
        question,
        system_prompt=_grounded_system_prompt(department.persona_system_prompt),
    )
    return ChatResponse(answer=answer)


@router.post("/{department_id}/trainer", response_model=TrainerResponse)
async def department_trainer(
    department_id: str,
    request: DepartmentChatRequest,
) -> TrainerResponse:
    department = get_department(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    question = f"[{department.name}] {request.question.strip()}"
    context = await retrieve_context(question, top_k=6)

    rag = RAGService()
    answer = await rag.generate(
        context,
        question,
        system_prompt=_grounded_system_prompt(department.trainer_persona_prompt),
    )
    return TrainerResponse(answer=answer)
