"""
Fallback LLM Provider

Decorator/Wrapper provider that delegates calls to a primary provider,
and transparently falls back to a secondary provider upon API errors.
"""

import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Type
from backend.LLM.LLMInterfaces import LLMInterface, T


class FallbackLLMProvider(LLMInterface):
    """Wrapper that tries primary provider first, fallback provider on failure."""

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

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        try:
            result = await self.primary.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                chat_history=chat_history,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
            self.last_model_used = getattr(self.primary, "last_model_used", None) or getattr(self.primary, "model_name", None)
            return result
        except Exception as e:
            if self.fallback:
                self.logger.warning("Primary LLM Provider failed (%s). Falling back to secondary provider", e)
                result = await self.fallback.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    chat_history=chat_history,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                self.last_model_used = getattr(self.fallback, "last_model_used", None) or getattr(self.fallback, "model_name", None)
                return result
            raise e

    async def generate_text_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, str]]:
        try:
            primary_iter = self.primary.generate_text_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                chat_history=chat_history,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
            async for chunk in primary_iter:
                self.last_model_used = getattr(self.primary, "last_model_used", None) or getattr(self.primary, "model_name", None)
                yield chunk
            self.last_model_used = getattr(self.primary, "last_model_used", None) or getattr(self.primary, "model_name", None)
            return
        except Exception as e:
            if self.fallback:
                self.logger.warning("Primary LLM Provider stream failed (%s). Falling back to secondary provider", e)
                fallback_iter = self.fallback.generate_text_stream(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    chat_history=chat_history,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                async for chunk in fallback_iter:
                    self.last_model_used = getattr(self.fallback, "last_model_used", None) or getattr(self.fallback, "model_name", None)
                    yield chunk
                self.last_model_used = getattr(self.fallback, "last_model_used", None) or getattr(self.fallback, "model_name", None)
                return
            raise e

    async def generate_structured_output(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        try:
            result = await self.primary.generate_structured_output(
                prompt=prompt,
                response_schema=response_schema,
                system_prompt=system_prompt,
                temperature=temperature,
            )
            self.last_model_used = getattr(self.primary, "last_model_used", None) or getattr(self.primary, "model_name", None)
            return result
        except Exception as e:
            if self.fallback:
                self.logger.warning("Primary LLM Provider failed (%s). Falling back to secondary provider", e)
                result = await self.fallback.generate_structured_output(
                    prompt=prompt,
                    response_schema=response_schema,
                    system_prompt=system_prompt,
                    temperature=temperature,
                )
                self.last_model_used = getattr(self.fallback, "last_model_used", None) or getattr(self.fallback, "model_name", None)
                return result
            raise e

    async def generate_structured_output_stream(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        try:
            primary_iter = self.primary.generate_structured_output_stream(
                prompt=prompt,
                response_schema=response_schema,
                system_prompt=system_prompt,
                temperature=temperature,
            )
            async for chunk in primary_iter:
                self.last_model_used = getattr(self.primary, "last_model_used", None) or getattr(self.primary, "model_name", None)
                yield chunk
            self.last_model_used = getattr(self.primary, "last_model_used", None) or getattr(self.primary, "model_name", None)
            return
        except Exception as e:
            if self.fallback:
                self.logger.warning("Primary LLM Provider structured stream failed (%s). Falling back to secondary provider", e)
                fallback_iter = self.fallback.generate_structured_output_stream(
                    prompt=prompt,
                    response_schema=response_schema,
                    system_prompt=system_prompt,
                    temperature=temperature,
                )
                async for chunk in fallback_iter:
                    self.last_model_used = getattr(self.fallback, "last_model_used", None) or getattr(self.fallback, "model_name", None)
                    yield chunk
                self.last_model_used = getattr(self.fallback, "last_model_used", None) or getattr(self.fallback, "model_name", None)
                return
            raise e

    def health_check(self) -> bool:
        return self.primary.health_check() or (self.fallback.health_check() if self.fallback else False)
