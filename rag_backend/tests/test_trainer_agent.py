"""Tests for TrainerSubAgent fallback behavior and persona propagation."""
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.trainer_agent import TrainerSubAgent


@pytest.mark.asyncio
async def test_trainer_returns_offline_fallback_when_lm_studio_unreachable():
    agent = TrainerSubAgent()
    request = httpx.Request("POST", "http://localhost:1234/v1/chat/completions")
    connect_error = httpx.ConnectError("connection refused", request=request)

    with patch.object(
        agent,
        "_refresh_google_drive_sources",
        new=AsyncMock(return_value={"enabled": True, "refreshed": 0, "skipped": 1, "errors": []}),
    ), patch.object(
        agent,
        "_refresh_core_sources",
        new=AsyncMock(return_value={"refreshed": 0, "skipped": 3, "errors": []}),
    ), patch.object(
        agent,
        "_build_google_drive_source_digest",
        return_value="Source: drive://doc\nContent: onboarding schedule and required forms",
    ), patch.object(
        agent,
        "_post_chat_completion",
        new=AsyncMock(side_effect=connect_error),
    ), patch.object(
        agent,
        "_search_google_drive_knowledge",
        return_value={
            "count": 1,
            "items": [
                {
                    "title": "Onboarding Checklist",
                    "source_url": "https://drive.google.com/file/d/abc/view",
                    "content_excerpt": "Complete forms, security training, and manager intro during week one.",
                }
            ],
        },
    ), patch.object(
        agent,
        "_search_training_data",
        return_value={
            "count": 1,
            "items": [
                {
                    "chunk_id": "chunk-1",
                    "title": "Week 1 Plan",
                    "topic": "onboarding",
                    "content": "Day 1 orientation, Day 2 systems access, Day 3 compliance review.",
                    "tags": "onboarding",
                }
            ],
        },
    ), patch.object(
        agent,
        "_search_core_web_knowledge",
        return_value={"count": 0, "items": []},
    ):
        answer = await agent.answer("What should I do in my first week?", history=[])

    assert "LM Studio is unavailable" in answer
    assert "Most relevant evidence" in answer
    assert "Onboarding Checklist" in answer
    assert "Week 1 Plan" in answer


@pytest.mark.asyncio
async def test_trainer_uses_system_prompt_override_in_messages():
    """system_prompt_override replaces the default Trainer system message."""
    agent = TrainerSubAgent()
    custom_prompt = "You are the Finance Trainer sub-agent focused on accounting."
    captured_messages: list = []

    async def _fake_post(client, url, payload):
        captured_messages.extend(payload["messages"])
        return {
            "choices": [{"message": {"content": "answer", "tool_calls": None}}],
            "finish_reason": "stop",
        }

    with patch.object(
        agent,
        "_refresh_google_drive_sources",
        new=AsyncMock(return_value={"enabled": False, "refreshed": 0, "skipped": 0, "errors": []}),
    ), patch.object(
        agent,
        "_refresh_core_sources",
        new=AsyncMock(return_value={"refreshed": 0, "skipped": 0, "errors": []}),
    ), patch.object(
        agent,
        "_build_google_drive_source_digest",
        return_value="No Google Drive knowledge snapshots available.",
    ), patch.object(
        agent,
        "_recall_previous_training_response",
        return_value={"found": False},
    ), patch.object(
        agent,
        "_post_chat_completion",
        side_effect=_fake_post,
    ):
        await agent.answer("Explain month-end close.", system_prompt_override=custom_prompt)

    system_message = next((m for m in captured_messages if m["role"] == "system"), None)
    assert system_message is not None, "No system message was sent to LM Studio"
    assert system_message["content"] == custom_prompt


@pytest.mark.asyncio
async def test_trainer_uses_default_system_prompt_when_no_override():
    """Without system_prompt_override the built-in Trainer identity is used."""
    agent = TrainerSubAgent()
    captured_messages: list = []

    async def _fake_post(client, url, payload):
        captured_messages.extend(payload["messages"])
        return {
            "choices": [{"message": {"content": "answer", "tool_calls": None}}],
            "finish_reason": "stop",
        }

    with patch.object(
        agent,
        "_refresh_google_drive_sources",
        new=AsyncMock(return_value={"enabled": False, "refreshed": 0, "skipped": 0, "errors": []}),
    ), patch.object(
        agent,
        "_refresh_core_sources",
        new=AsyncMock(return_value={"refreshed": 0, "skipped": 0, "errors": []}),
    ), patch.object(
        agent,
        "_build_google_drive_source_digest",
        return_value="No Google Drive knowledge snapshots available.",
    ), patch.object(
        agent,
        "_recall_previous_training_response",
        return_value={"found": False},
    ), patch.object(
        agent,
        "_post_chat_completion",
        side_effect=_fake_post,
    ):
        await agent.answer("Generic question.")

    system_message = next((m for m in captured_messages if m["role"] == "system"), None)
    assert system_message is not None
    assert "Trainer" in system_message["content"]
