import asyncio
from typing import Any

import structlog

from ideaforge.core.exceptions import AgentError

logger = structlog.get_logger(__name__)

_RETRY_DELAYS = (1.0, 2.0, 4.0)  # seconds between attempts


class BaseAgent:
    """Mixin that adds asyncio timeout + exponential-backoff retry to any LangChain chain."""

    # Override in subclasses to set a tighter per-attempt wall-clock limit.
    # asyncio.wait_for enforces this regardless of whether the LLM SDK honors its own timeout.
    _invoke_timeout: float = 180.0

    async def _invoke_with_retry(self, chain: Any, inputs: dict) -> Any:
        last_exc: Exception | None = None
        for attempt, delay in enumerate(_RETRY_DELAYS, start=1):
            try:
                return await asyncio.wait_for(
                    chain.ainvoke(inputs), timeout=self._invoke_timeout
                )
            except asyncio.TimeoutError as exc:
                last_exc = exc
                logger.warning(
                    "agent.timeout",
                    agent=type(self).__name__,
                    attempt=attempt,
                    timeout=self._invoke_timeout,
                )
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "agent.retry",
                    agent=type(self).__name__,
                    attempt=attempt,
                    max_attempts=len(_RETRY_DELAYS),
                    error=str(exc),
                )
            if attempt < len(_RETRY_DELAYS):
                await asyncio.sleep(delay)

        raise AgentError(
            f"{type(self).__name__} failed after {len(_RETRY_DELAYS)} attempts"
        ) from last_exc
