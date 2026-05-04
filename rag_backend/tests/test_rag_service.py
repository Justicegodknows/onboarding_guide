"""Tests for RAGService generation error handling."""
from unittest.mock import AsyncMock, patch

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
