from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_chain import build_llm_chain, retrieve_context
from prompts.builder import build_simple_prompt
from prompts.postprocess import strip_scratchpad

router = APIRouter(prefix="/api/v1/chat")


@router.post("/")
async def chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    q = request.question
    dept = current_user.get("dept")
    ctx = await retrieve_context(q, top_k=6)

    # 3. Invoke the LLM chain with the fully-resolved input dict.
    prompt = build_simple_prompt() if request.simple_mode else None
    llm_chain = build_llm_chain(prompt)
    raw = await llm_chain.ainvoke({
        "question": q,
        "context": ctx,
        "user_department": dept or "General",
        "user_role": current_user.get("role", "USER"),
        "company_name": "VaultMind Demo Corp",
        "fallback_contact": "your team lead or HR",
    })

    # 4. Strip CoT scratchpad blocks before returning to the client.
    public_answer = strip_scratchpad(raw)
    return ChatResponse(answer=public_answer)
