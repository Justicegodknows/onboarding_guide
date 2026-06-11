from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.schemas import AgentChatRequest, AgentChatResponse
from app.services.agent_retrieval import retrieve_context_with_sources
from app.services.nemoclaw_adapter import NemoclawAdapter, NemoclawExecutionError

router = APIRouter(prefix="/agent", tags=["agent"])

_adapter = NemoclawAdapter()


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    request: AgentChatRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = await _adapter.run_agent_chat(
            message=request.message,
            conversation_id=request.conversation_id,
            user_claims=current_user,
            retrieve_tool=retrieve_context_with_sources,
        )
        return AgentChatResponse(**result)
    except NemoclawExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
