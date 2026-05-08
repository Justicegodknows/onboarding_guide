from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.rag_service import RAGService
from langchain_core.prompts import ChatPromptTemplate

from prompts.builder import build_simple_prompt, build_vaultmind_prompt
from prompts.postprocess import strip_scratchpad


def format_chunks_with_metadata(docs: List[Document]) -> str:
    """Render retrieved documents into a citation-rich context string.

    Each chunk is prefixed with a bracketed citation built from the source file
    name and whatever page / section metadata is present, e.g.:

        [Employee_Handbook.pdf, p.12]
        <chunk text>

    The assembled string is injected into the {context} slot of the prompt.
    """
    if not docs:
        return "(no relevant chunks returned for this user's access scope)"

    pieces: List[str] = []
    for doc in docs:
        meta = doc.metadata
        source = meta.get("source", "unknown")
        page = meta.get("page", "")
        section = meta.get("section", "")

        citation = source
        if page:
            citation += f", p.{page}"
        if section:
            citation += f", §{section}"

        pieces.append(f"[{citation}]\n{doc.page_content}")

    return "\n\n".join(pieces)


def _build_llm() -> ChatOpenAI:
    """Return a ChatOpenAI instance pointing at NVIDIA NIM or LM Studio.

    Priority:
      1. NVIDIA NIM  — used when NVIDIA_API_KEY is set.
      2. LM Studio   — local fallback, no API key required.
    """
    if settings.NVIDIA_API_KEY:
        return ChatOpenAI(
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NVIDIA_BASE_URL,
            model=settings.NVIDIA_CHAT_MODEL,
            temperature=0.2,
            max_tokens=700,
        )
    return ChatOpenAI(
        api_key=settings.LLM_API_KEY or "no-key-needed",
        base_url=f"{settings.LM_STUDIO_BASE_URL.rstrip('/')}/v1",
        model=settings.LM_STUDIO_MODEL,
        temperature=0.2,
        max_tokens=700,
    )


def build_rag_chain(
    current_user: Dict[str, Any],
    retriever=None,
    prompt: ChatPromptTemplate | None = None,
):
    """Assemble the VaultMind RAG chain for a single request.

    Wires together: retrieval → citation formatting → prompting →
    generation → scratchpad stripping, using LangChain LCEL.

    Args:
        current_user: dict from get_current_user — keys: id, role, dept, display_name.
        retriever: optional LangChain retriever; defaults to ChromaDB similarity
                   retriever filtered to the user's department (top-4 chunks).
        prompt: optional ChatPromptTemplate to use instead of the default.
                Pass ``build_simple_prompt()`` for a lightweight chain without
                CoT / few-shot examples, or ``build_vaultmind_prompt()`` (default)
                for the full chain with chain-of-thought and few-shot examples.

    Returns:
        An LCEL Runnable whose input is the question string and whose output
        is the final answer string (scratchpad removed).

    Usage:
        # Full chain (CoT + few-shot):
        chain = build_rag_chain(current_user)

        # Lightweight chain (system prompt only):
        from prompts.builder import build_simple_prompt
        chain = build_rag_chain(current_user, prompt=build_simple_prompt())

        answer = await chain.ainvoke(question)
    """
    if retriever is None:
        rag = RAGService()
        dept = current_user.get("dept")
        retriever = rag.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 4,
                **({"filter": {"department": dept}} if dept else {}),
            },
        )

    resolved_prompt = prompt if prompt is not None else build_vaultmind_prompt()
    llm = _build_llm()

    chain = (
        {
            "context": retriever | format_chunks_with_metadata,
            "question": RunnablePassthrough(),
            "user_department": lambda _: current_user.get("dept", "General"),
            "user_role": lambda _: current_user.get("role", "USER"),
            "company_name": lambda _: "VaultMind Demo Corp",
            "fallback_contact": lambda _: "your team lead or HR",
        }
        | resolved_prompt
        | llm
        | StrOutputParser()
        | strip_scratchpad
    )

    return chain


def build_llm_chain(prompt: ChatPromptTemplate | None = None):
    """Return a prompt → LLM → str chain with no retriever attached.

    The caller is responsible for fetching and formatting context before
    invoking this chain.  Input dict keys must include:
        context, question, user_department, user_role, company_name, fallback_contact

    The chain does NOT strip the scratchpad — call strip_scratchpad() on the
    returned string so the caller controls exactly when that happens.

    Usage (in a FastAPI route)::

        llm_chain = build_llm_chain(prompt)
        raw = await llm_chain.ainvoke({"question": q, "context": ctx, ...})
        public_answer = strip_scratchpad(raw)
    """
    resolved_prompt = prompt if prompt is not None else build_vaultmind_prompt()
    return resolved_prompt | _build_llm() | StrOutputParser()
