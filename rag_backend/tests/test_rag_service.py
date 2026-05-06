"""Tests for RAGService generation error handling and persona propagation."""
from unittest.mock import AsyncMock, MagicMock, call, patch

import httpx
import pytest

from app.services.rag_service import RAGService


@pytest.mark.asyncio
async def test_generate_returns_helpful_message_on_lm_studio_401():
    service = RAGService()
    request = httpx.Request("POST", "http://localhost:1234/v1/chat/completions")
    response = httpx.Response(401, request=request)
    error = httpx.HTTPStatusError("Unauthorized", request=request, response=response)

    with patch.object(
        service,
        "_generate_via_openai_compat",
        new=AsyncMock(side_effect=error),
    ):
        result = await service.generate("", "Hello?")

    assert "401 Unauthorized" in result
    assert "LM Studio" in result


@pytest.mark.asyncio
async def test_generate_uses_custom_system_prompt_in_messages():
    """system_prompt kwarg replaces the default system message sent to LM Studio."""
    service = RAGService()
    custom_prompt = "You are the HR onboarding assistant with empathetic guidance."
    captured: list = []

    async def _fake_generate(messages, settings):
        captured.extend(messages)
        return "answer"

    with patch.object(service, "_generate_via_openai_compat", side_effect=_fake_generate):
        await service.generate("some context", "a question", system_prompt=custom_prompt)

    assert captured[0]["role"] == "system"
    assert captured[0]["content"] == custom_prompt


@pytest.mark.asyncio
async def test_generate_uses_default_system_prompt_when_none_given():
    """Without a system_prompt kwarg the default onboarding assistant message is used."""
    service = RAGService()
    captured: list = []

    async def _fake_generate(messages, settings):
        captured.extend(messages)
        return "answer"

    with patch.object(service, "_generate_via_openai_compat", side_effect=_fake_generate):
        await service.generate("ctx", "q")

    assert captured[0]["role"] == "system"
    assert "onboarding" in captured[0]["content"].lower()


@pytest.mark.asyncio
async def test_generate_embeds_context_and_question_in_user_message():
    """Context and question both appear inside the user message payload."""
    service = RAGService()
    captured: list = []

    async def _fake_generate(messages, settings):
        captured.extend(messages)
        return "answer"

    with patch.object(service, "_generate_via_openai_compat", side_effect=_fake_generate):
        await service.generate("UNIQUE_CONTEXT_TEXT", "UNIQUE_QUESTION_TEXT")

    user_msg = next(m for m in captured if m["role"] == "user")
    assert "UNIQUE_CONTEXT_TEXT" in user_msg["content"]
    assert "UNIQUE_QUESTION_TEXT" in user_msg["content"]
