# rag_backend/app/routers/chat.py
#
# Level 3 -- End User chat / query endpoint
# Any authenticated user can call this.
# Results are automatically scoped to the caller's tenant AND department.

from fastapi import APIRouter, Depends

from app.core.permissions import require_user, get_user_scope
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import RAGService
from app.services.rag_chain import build_llm_chain
from prompts.builder import build_simple_prompt
from prompts.postprocess import strip_scratchpad

router = APIRouter(prefix="/api/v1/chat")


@router.post("/")
async def chat_endpoint(
    request: ChatRequest,
    current_user: dict = Depends(require_user),
):
    """
    Query documents using the RAG pipeline.

    Access is scoped automatically based on the caller's role:
      - USER         : results limited to their tenant AND their department
      - TENANT_ADMIN : results limited to their tenant (all departments)
      - SUPER_ADMIN  : no restrictions (sees all tenants)
    """
    q = request.question

    # Resolve the effective scope from the caller's role and JWT claims
    scope = get_user_scope(current_user)
    tenant_id  = scope["tenant_id"]
    department = scope["department"]

    # Build a ChromaDB metadata filter -- only apply fields that are set
    filter_metadata: dict | None = None
    if department:
        filter_metadata = {"department": department}

    # Retrieve from the tenant-scoped ChromaDB collection
    # RAGService(tenant_id=...) routes to collection "tenant_{tenant_id}_docs"
    rag = RAGService(tenant_id=tenant_id)
    docs = rag.retrieve(
        query=q,
        top_k=6,
        filter_metadata=filter_metadata,
    )
    ctx = [d["content"] for d in docs]

    # Build the LLM chain and generate the answer
    prompt = build_simple_prompt() if request.simple_mode else None
    llm_chain = build_llm_chain(prompt)
    raw = await llm_chain.ainvoke({
        "question": q,
        "context": ctx,
        "user_department": department or "General",
        "user_role": current_user.get("role", "USER"),
        "company_name": "VaultMind",
        "fallback_contact": "your team lead or HR",
    })

    public_answer = strip_scratchpad(raw)
    return ChatResponse(answer=public_answer)
