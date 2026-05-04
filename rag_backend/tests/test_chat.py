"""Tests for POST /api/v1/chat/."""
import pytest
from unittest.mock import AsyncMock, patch


def test_chat_returns_answer(client):
    with patch(
        "app.routers.chat.RAGService.generate",
        new_callable=AsyncMock,
        return_value="This is the onboarding answer.",
    ):
        response = client.post(
            "/api/v1/chat/",
            json={"question": "What is the onboarding process?"},
        )

    assert response.status_code == 200
    assert response.json() == {"answer": "This is the onboarding answer."}


def test_chat_accepts_history_field(client):
    with patch(
        "app.routers.chat.RAGService.generate",
        new_callable=AsyncMock,
        return_value="Answer",
    ):
        response = client.post(
            "/api/v1/chat/",
            json={
                "question": "Follow-up question",
                "history": ["previous question"],
            },
        )

    assert response.status_code == 200


def test_chat_missing_question_returns_422(client):
    response = client.post("/api/v1/chat/", json={})
    assert response.status_code == 422


def test_chat_raises_on_unexpected_error(client):
    """Unhandled exceptions from generate() propagate as server errors."""
    with patch(
        "app.routers.chat.RAGService.generate",
        new_callable=AsyncMock,
        side_effect=RuntimeError("unexpected bug"),
    ):
        with pytest.raises(RuntimeError, match="unexpected bug"):
            client.post(
                "/api/v1/chat/",
                json={"question": "Will this fail?"},
            )
