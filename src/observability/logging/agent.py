from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

from src.observability.logging.logger import get_agent_logger

logger = get_agent_logger()


class AgentLoggingCallback(AsyncCallbackHandler):
    raise_error = False

    async def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._start_times: dict[str, float] = getattr(self, "_start_times", {})
        self._start_times[str(run_id)] = time.perf_counter()
        logger.info(
            "LLM invocation started",
            extra={
                "extra_data": {
                    "event": "llm_start",
                    "run_id": str(run_id),
                    "parent_run_id": str(parent_run_id) if parent_run_id else None,
                    "model": serialized.get("id", [None])[-1],
                    "prompt_count": len(prompts),
                }
            },
        )

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        start = getattr(self, "_start_times", {}).pop(str(run_id), None)
        duration_ms = round((time.perf_counter() - start) * 1000, 2) if start else None

        token_usage = {}
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})

        logger.info(
            "LLM invocation completed",
            extra={
                "extra_data": {
                    "event": "llm_end",
                    "run_id": str(run_id),
                    "duration_ms": duration_ms,
                    "token_usage": token_usage or None,
                }
            },
        )

    async def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        logger.error(
            "LLM invocation failed",
            exc_info=error,
            extra={
                "extra_data": {
                    "event": "llm_error",
                    "run_id": str(run_id),
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            },
        )

    async def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._start_times = getattr(self, "_start_times", {})
        self._start_times[str(run_id)] = time.perf_counter()
        logger.info(
            "Tool invocation started",
            extra={
                "extra_data": {
                    "event": "tool_start",
                    "run_id": str(run_id),
                    "parent_run_id": str(parent_run_id) if parent_run_id else None,
                    "tool_name": serialized.get("name"),
                }
            },
        )

    async def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        start = getattr(self, "_start_times", {}).pop(str(run_id), None)
        duration_ms = round((time.perf_counter() - start) * 1000, 2) if start else None
        logger.info(
            "Tool invocation completed",
            extra={
                "extra_data": {
                    "event": "tool_end",
                    "run_id": str(run_id),
                    "duration_ms": duration_ms,
                    "output_length": len(output) if output else 0,
                }
            },
        )

    async def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        logger.error(
            "Tool invocation failed",
            exc_info=error,
            extra={
                "extra_data": {
                    "event": "tool_error",
                    "run_id": str(run_id),
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            },
        )

    async def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._start_times = getattr(self, "_start_times", {})
        self._start_times[str(run_id)] = time.perf_counter()
        logger.debug(
            "Chain/graph started",
            extra={
                "extra_data": {
                    "event": "chain_start",
                    "run_id": str(run_id),
                    "parent_run_id": str(parent_run_id) if parent_run_id else None,
                    "chain_type": serialized.get("id", [None])[-1],
                }
            },
        )

    async def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        start = getattr(self, "_start_times", {}).pop(str(run_id), None)
        duration_ms = round((time.perf_counter() - start) * 1000, 2) if start else None
        logger.debug(
            "Chain/graph completed",
            extra={
                "extra_data": {
                    "event": "chain_end",
                    "run_id": str(run_id),
                    "duration_ms": duration_ms,
                }
            },
        )

    async def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        logger.error(
            "Chain/graph failed",
            exc_info=error,
            extra={
                "extra_data": {
                    "event": "chain_error",
                    "run_id": str(run_id),
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                }
            },
        )
