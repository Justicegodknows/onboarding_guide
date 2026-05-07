"""Tests for the Pydantic schemas."""
import pytest
from pydantic import ValidationError

from app.models.schemas import ChatRequest, ChatResponse


class TestChatRequest:
    def test_requires_question(self):
        with pytest.raises(ValidationError):
            ChatRequest()  # type: ignore[call-arg]

    def test_question_stored_correctly(self):
        req = ChatRequest(question="Hello?")
        assert req.question == "Hello?"

    def test_history_defaults_to_none(self):
        req = ChatRequest(question="Hello?")
        assert req.history is None

    def test_history_accepts_list_of_strings(self):
        req = ChatRequest(question="Hello?", history=["q1", "q2"])
        assert req.history == ["q1", "q2"]


class TestChatResponse:
    def test_requires_answer(self):
        with pytest.raises(ValidationError):
            ChatResponse()  # type: ignore[call-arg]

    def test_answer_stored_correctly(self):
        resp = ChatResponse(answer="42")
        assert resp.answer == "42"
