"""
Fallback LLM Provider

Decorator/Wrapper provider that delegates calls to a primary provider,
and transparently falls back to a secondary provider upon API errors.
"""

import logging
from typing import Dict, Iterator, List, Optional, Type
from backend.LLM.LLMInterfaces import LLMInterface, T


class FallbackLLMProvider(LLMInterface):
    """Wrapper that tries primary provider first, fallback provider on failure."""

    def __init__(self, primary_provider: LLMInterface, fallback_provider: Optional[LLMInterface] = None):
        self.primary = primary_provider
        self.fallback = fallback_provider
        self.logger = logging.getLogger(__name__)

    @property
    def model_name(self) -> str:
        return getattr(self.primary, "model_name", "fallback-provider")

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        try:
            return self.primary.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                chat_history=chat_history,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
        except Exception as e:
            if self.fallback:
                self.logger.warning("Primary LLM Provider failed (%s). Falling back to secondary provider", e)
                return self.fallback.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    chat_history=chat_history,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
            raise e

    def generate_text_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[Dict[str, str]]:
        try:
            primary_iter = self.primary.generate_text_stream(
                prompt=prompt,
                system_prompt=system_prompt,
                chat_history=chat_history,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
            for chunk in primary_iter:
                yield chunk
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
                for chunk in fallback_iter:
                    yield chunk
                return
            raise e

    def generate_structured_output(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        try:
            return self.primary.generate_structured_output(
                prompt=prompt,
                response_schema=response_schema,
                system_prompt=system_prompt,
                temperature=temperature,
            )
        except Exception as e:
            if self.fallback:
                self.logger.warning("Primary LLM Provider failed (%s). Falling back to secondary provider", e)
                return self.fallback.generate_structured_output(
                    prompt=prompt,
                    response_schema=response_schema,
                    system_prompt=system_prompt,
                    temperature=temperature,
                )
            raise e

    def health_check(self) -> bool:
        return self.primary.health_check() or (self.fallback.health_check() if self.fallback else False)
