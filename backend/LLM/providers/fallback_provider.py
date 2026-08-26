"""
Fallback LLM Provider

Decorator/Wrapper provider that delegates calls to a primary provider, and
transparently falls back to a secondary provider upon *availability* failures.

Two guarantees beyond a naive try/except:

1. Only retryable failures trigger a fallback (see backend.LLM.errors).
   A malformed prompt or a schema violation fails identically on the secondary
   provider, so falling back would double latency and cost for nothing.

2. A stream only falls back while nothing has been emitted yet. Once the client
   has received tokens, restarting on another provider would splice two
   different completions into one visibly corrupted response; the error is
   raised instead so the caller can handle a partial stream explicitly.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Type

from backend.LLM.errors import describe, is_retryable
from backend.LLM.LLMInterfaces import LLMInterface, T


class FallbackLLMProvider(LLMInterface):
    """Wrapper that tries the primary provider first, then the fallback."""

    def __init__(self, primary_provider: LLMInterface, fallback_provider: Optional[LLMInterface] = None):
        self.primary = primary_provider
        self.fallback = fallback_provider
        self.logger = logging.getLogger(__name__)
        # Set after each generate_* call: the model name that actually served
        # the request, so callers can persist which provider produced a
        # GO/NO-GO decision when a silent fallback occurred.
        self.last_model_used: Optional[str] = None

    @property
    def model_name(self) -> str:
        return getattr(self.primary, "model_name", "fallback-provider")

    def _record(self, provider: LLMInterface) -> None:
        self.last_model_used = getattr(provider, "last_model_used", None) or getattr(
            provider, "model_name", None
        )

    def _should_fallback(self, exc: Exception, operation: str) -> bool:
        """Decides whether `exc` warrants routing to the secondary provider."""
        if not self.fallback:
            return False
        if not is_retryable(exc):
            self.logger.error(
                "Primary LLM provider failed on %s with a non-retryable error (%s). "
                "Not falling back: the secondary provider would fail identically.",
                operation,
                describe(exc),
            )
            return False
        self.logger.warning(
            "Primary LLM provider unavailable on %s (%s). Routing to secondary provider.",
            operation,
            describe(exc),
        )
        return True

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        kwargs = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "chat_history": chat_history,
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        }
        try:
            result = await self.primary.generate_text(**kwargs)
            self._record(self.primary)
            return result
        except Exception as e:
            if not self._should_fallback(e, "generate_text"):
                raise
            result = await self.fallback.generate_text(**kwargs)
            self._record(self.fallback)
            return result

    async def generate_text_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, str]]:
        kwargs = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "chat_history": chat_history,
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        }
        emitted = False
        try:
            async for chunk in self.primary.generate_text_stream(**kwargs):
                emitted = True
                # Recorded per chunk, not just at the end: callers read
                # last_model_used *during* iteration (at the result event) to
                # persist which model served the request.
                self._record(self.primary)
                yield chunk
            self._record(self.primary)
            return
        except Exception as e:
            if emitted:
                # Mid-stream failure: the client already holds a prefix of the
                # primary completion. Restarting elsewhere would corrupt it.
                self.logger.error(
                    "Primary LLM provider failed mid-stream on generate_text_stream (%s). "
                    "Cannot fall back once tokens were emitted.",
                    describe(e),
                )
                raise
            if not self._should_fallback(e, "generate_text_stream"):
                raise

        async for chunk in self.fallback.generate_text_stream(**kwargs):
            self._record(self.fallback)
            yield chunk
        self._record(self.fallback)

    async def generate_structured_output(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        kwargs = {
            "prompt": prompt,
            "response_schema": response_schema,
            "system_prompt": system_prompt,
            "temperature": temperature,
        }
        try:
            result = await self.primary.generate_structured_output(**kwargs)
            self._record(self.primary)
            return result
        except Exception as e:
            if not self._should_fallback(e, "generate_structured_output"):
                raise
            result = await self.fallback.generate_structured_output(**kwargs)
            self._record(self.fallback)
            return result

    async def generate_structured_output_stream(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        kwargs = {
            "prompt": prompt,
            "response_schema": response_schema,
            "system_prompt": system_prompt,
            "temperature": temperature,
        }
        emitted = False
        try:
            async for chunk in self.primary.generate_structured_output_stream(**kwargs):
                emitted = True
                # See generate_text_stream: stream_llm_analyze reads
                # last_model_used at the 'result' event to persist the model
                # that produced the GO/NO-GO decision.
                self._record(self.primary)
                yield chunk
            self._record(self.primary)
            return
        except Exception as e:
            if emitted:
                self.logger.error(
                    "Primary LLM provider failed mid-stream on "
                    "generate_structured_output_stream (%s). "
                    "Cannot fall back once events were emitted.",
                    describe(e),
                )
                raise
            if not self._should_fallback(e, "generate_structured_output_stream"):
                raise

        async for chunk in self.fallback.generate_structured_output_stream(**kwargs):
            self._record(self.fallback)
            yield chunk
        self._record(self.fallback)

    def health_check(self) -> bool:
        return self.primary.health_check() or (
            self.fallback.health_check() if self.fallback else False
        )
