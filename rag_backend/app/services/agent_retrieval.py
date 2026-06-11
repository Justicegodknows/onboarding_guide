from __future__ import annotations

from typing import Any, Dict, List, Tuple

from langchain_core.documents import Document

from app.services.rag_service import RAGService
from app.services.rag_chain import format_chunks_with_metadata


def _build_rbac_filter(user_claims: Dict[str, Any]) -> Dict[str, Any] | None:
    """Build a Chroma metadata filter from JWT claims.

    Current policy:
    - ADMIN can retrieve across departments.
    - non-ADMIN is restricted to documents matching their `dept` claim.
    """
    role = (user_claims or {}).get("role")
    dept = (user_claims or {}).get("dept")

    if role == "ADMIN":
        return None
    if dept:
        return {"department": dept}
    return None


async def retrieve_context_with_sources(
    user_claims: Dict[str, Any],
    query: str,
    top_k: int = 6,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Retrieve RBAC-filtered context from existing Chroma and return sources.

    Reuses the existing RAGService/Chroma configuration and persistence path.
    """
    rag = RAGService()
    filter_metadata = _build_rbac_filter(user_claims)

    retriever = rag.vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": max(1, top_k),
            **({"filter": filter_metadata} if filter_metadata else {}),
        },
    )

    docs: List[Document] = await retriever.ainvoke(query)
    context = format_chunks_with_metadata(docs)

    sources: List[Dict[str, Any]] = []
    for doc in docs:
        meta = doc.metadata or {}
        source = str(meta.get("source", "unknown"))
        title = str(meta.get("title") or source)
        chunk_id = meta.get("chunk_id")
        sources.append(
            {
                "title": title,
                "source": source,
                "chunk_id": str(chunk_id) if chunk_id is not None else None,
            }
        )

    return context, sources
