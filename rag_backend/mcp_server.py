"""
MCP server that wraps the onboarding RAG backend.
LM Studio launches this via stdio (mcp.json command entry).
"""
import httpx
from mcp.server.fastmcp import FastMCP

BACKEND = "http://localhost:8000"

mcp = FastMCP("onboarding-rag")


@mcp.tool()
def health_check() -> dict:
    """Check whether the onboarding RAG backend is healthy."""
    with httpx.Client(timeout=10) as client:
        r = client.get(f"{BACKEND}/health")
        r.raise_for_status()
        return r.json()


@mcp.tool()
def chat_with_onboarding_rag(question: str, history: list[str] | None = None) -> dict:
    """Ask the onboarding RAG assistant a question."""
    with httpx.Client(timeout=60) as client:
        r = client.post(
            f"{BACKEND}/api/v1/chat/",
            json={"question": question, "history": history or []},
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
def trainer_agent_answer(question: str, history: list[str] | None = None) -> dict:
    """Ask the trainer sub-agent for training-focused answers."""
    with httpx.Client(timeout=60) as client:
        r = client.post(
            f"{BACKEND}/api/v1/trainer/",
            json={"question": question, "history": history or []},
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
def upload_document_text(filename: str, content: str) -> dict:
    """Upload a text document to the backend knowledge base."""
    with httpx.Client(timeout=30) as client:
        r = client.post(
            f"{BACKEND}/api/v1/documents/upload",
            json={"filename": filename, "content": content},
        )
        r.raise_for_status()
        return r.json()


@mcp.tool()
def trigger_ingestion() -> dict:
    """Trigger ingestion of knowledge chunks from help/chunks.json into the KB."""
    with httpx.Client(timeout=60) as client:
        r = client.post(f"{BACKEND}/api/v1/ingest/")
        r.raise_for_status()
        return r.json()


@mcp.tool()
def get_onboarding_progress(user_id: str) -> dict:
    """Get onboarding progress for a user."""
    with httpx.Client(timeout=10) as client:
        r = client.get(f"{BACKEND}/api/v1/onboarding/{user_id}")
        r.raise_for_status()
        return r.json()


@mcp.tool()
def complete_onboarding_step(user_id: str, step_id: int) -> dict:
    """Mark an onboarding step as complete for a user. step_id must be 1–6."""
    with httpx.Client(timeout=10) as client:
        r = client.post(
            f"{BACKEND}/api/v1/onboarding/{user_id}/complete/{step_id}"
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    mcp.run()
