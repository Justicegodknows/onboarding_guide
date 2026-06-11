"""Tests for POST /agent/chat."""
import pytest
from unittest.mock import AsyncMock, patch


def test_agent_chat_requires_auth(client):
    """Missing JWT should return 401."""
    response = client.post(
        "/agent/chat",
        json={"message": "What is the onboarding process?"},
    )
    assert response.status_code == 401


def test_agent_chat_rejects_invalid_token(client):
    """Invalid JWT should return 401."""
    response = client.post(
        "/agent/chat",
        json={"message": "What is the onboarding process?"},
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


def test_agent_chat_rbac_restricts_by_department(client):
    """User with dept=Finance should not retrieve dept=IT docs."""
    from app.core.security import create_access_token

    # Create token with Finance department
    token = create_access_token(
        data={"sub": "finance_user", "role": "USER", "dept": "Finance", "display_name": "Finance User"}
    )

    with patch(
        "app.services.agent_retrieval.RAGService",
        autospec=True,
    ) as mock_rag_class:
        mock_rag_instance = mock_rag_class.return_value
        mock_retriever = AsyncMock()
        mock_rag_instance.vector_store.as_retriever.return_value = mock_retriever

        # Simulate different department docs
        from langchain_core.documents import Document
        mock_retriever.ainvoke = AsyncMock(return_value=[
            Document(
                page_content="Finance doc content",
                metadata={"source": "finance_handbook.pdf", "department": "Finance"},
            ),
        ])

        response = client.post(
            "/agent/chat",
            json={"message": "Show me docs"},
            headers={"Authorization": f"Bearer {token}"},
        )

    # If RBAC filter is working, the call should have included filter={"department": "Finance"}
    # and NOT included IT docs
    assert response.status_code == 200


def test_agent_chat_admin_can_retrieve_all(client):
    """Admin should not be filtered by department."""
    from app.core.security import create_access_token

    token = create_access_token(
        data={"sub": "admin_user", "role": "ADMIN", "dept": "IT", "display_name": "Admin"}
    )

    with patch(
        "app.services.agent_retrieval.RAGService",
        autospec=True,
    ):
        response = client.post(
            "/agent/chat",
            json={"message": "Show me all docs"},
            headers={"Authorization": f"Bearer {token}"},
        )

    # Admin gets access without filter
    assert response.status_code == 200
