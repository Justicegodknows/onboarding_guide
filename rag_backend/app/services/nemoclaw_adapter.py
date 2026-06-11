from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.config import settings
from app.services.rag_chain import build_llm_chain
from prompts.builder import build_simple_prompt
from prompts.postprocess import strip_scratchpad

logger = logging.getLogger(__name__)

SAFE_TOOL_ALLOWLIST = {"retrieve_context"}


class NemoclawExecutionError(Exception):
    """Raised when Nemoclaw execution fails cleanly."""


class NemoclawAdapter:
    """Adapter for Nemoclaw sandbox-backed chat orchestration.

    This implementation is intentionally read-only and only exposes allowlisted
    retrieval capability. It avoids any ingestion/admin action routing.
    """

    def __init__(self) -> None:
        self.sandbox_name = settings.NEMOCLAW_SANDBOX_NAME
        self.timeout_seconds = settings.NEMOCLAW_TIMEOUT_SECONDS

    async def run_agent_chat(
        self,
        *,
        message: str,
        conversation_id: Optional[str],
        user_claims: Dict[str, Any],
        retrieve_tool: Callable[[Dict[str, Any], str], Awaitable[tuple[str, List[Dict[str, Any]]]]],
    ) -> Dict[str, Any]:
        del conversation_id  # reserved for future sandbox session threading

        try:
            return await asyncio.wait_for(
                self._execute_read_only_agent(
                    message=message,
                    user_claims=user_claims,
                    retrieve_tool=retrieve_tool,
                ),
                timeout=self.timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            logger.warning(
                "Nemoclaw timeout (sandbox=%s, timeout=%ss, user=%s)",
                self.sandbox_name,
                self.timeout_seconds,
                user_claims.get("id"),
            )
            raise NemoclawExecutionError("Nemoclaw agent timed out. Please retry.") from exc
        except NemoclawExecutionError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Nemoclaw execution failure (sandbox=%s, user=%s, role=%s, dept=%s): %s",
                self.sandbox_name,
                user_claims.get("id"),
                user_claims.get("role"),
                user_claims.get("dept"),
                exc.__class__.__name__,
            )
            raise NemoclawExecutionError("Nemoclaw agent is temporarily unavailable.") from exc

    async def _execute_read_only_agent(
        self,
        *,
        message: str,
        user_claims: Dict[str, Any],
        retrieve_tool: Callable[[Dict[str, Any], str], Awaitable[tuple[str, List[Dict[str, Any]]]]],
    ) -> Dict[str, Any]:
        tool_name = "retrieve_context"
        if tool_name not in SAFE_TOOL_ALLOWLIST:
            raise NemoclawExecutionError("Requested tool is not allowlisted.")

        context, sources = await retrieve_tool(user_claims, message)

        llm_chain = build_llm_chain(build_simple_prompt())
        raw = await llm_chain.ainvoke(
            {
                "question": message,
                "context": context,
                "user_department": user_claims.get("dept", "General"),
                "user_role": user_claims.get("role", "USER"),
                "company_name": "VaultMind Demo Corp",
                "fallback_contact": "your team lead or HR",
            }
        )
        answer = strip_scratchpad(raw)

        return {
            "answer": answer,
            "sources": sources,
        }
