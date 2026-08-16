"""
Gemini LLM Provider

Concrete provider for Google Gemini models with multi-key round robin and Pydantic structured output.
"""

import time
from typing import Dict, Iterator, List, Optional, Type
from pydantic import BaseModel
import litellm

from backend import config
from backend.LLM.providers.base_provider import BaseLLMProvider
from backend.LLM.LLMInterfaces import T


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider with multi-key failover and structured output."""

    def __init__(self, model_name: str = "gemini/gemini-2.5-flash", temperature: float = 0.0):
        # Clean model prefix if raw name passed
        clean_model = model_name if model_name.startswith("gemini/") else f"gemini/{model_name}"
        super().__init__(model_name=clean_model, temperature=temperature)
        
        self.api_keys = [key for key in [config.GEMINI_API_KEY_1, config.GEMINI_API_KEY_2] if key]
        if not self.api_keys:
            self.api_keys = ["dummy-key"]

    def _execute_with_keys(self, func, **kwargs):
        """Executes API call, switching keys if rate limit / quota is exceeded."""
        last_exception = None
        for key in self.api_keys:
            try:
                return func(api_key=key, **kwargs)
            except Exception as e:
                self.logger.warning("Gemini API key failed (%s). Trying next key...", e)
                last_exception = e
        if last_exception:
            raise last_exception

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature

        def _call(api_key: str):
            start_time = time.perf_counter()
            response = litellm.completion(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                max_tokens=max_output_tokens,
                api_key=api_key,
            )
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            usage = getattr(response, "usage", None)
            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

            self.logger.info(
                "Gemini LLM text call completed | model=%s duration_ms=%.2f prompt_tokens=%d completion_tokens=%d total_tokens=%d",
                self.model_name,
                duration_ms,
                prompt_tokens,
                completion_tokens,
                total_tokens,
            )
            return response.choices[0].message.content

        return self._execute_with_keys(_call)

    def generate_text_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[Dict[str, str]]:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature

        last_exception = None
        for key in self.api_keys:
            try:
                response = litellm.completion(
                    model=self.model_name,
                    messages=messages,
                    temperature=temp,
                    max_tokens=max_output_tokens,
                    api_key=key,
                    stream=True,
                    timeout=60,
                )
                start_time = time.perf_counter()
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta:
                        content = getattr(chunk.choices[0].delta, "content", "") or ""
                        if content:
                            yield {"type": "token", "content": content}
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                self.logger.info(
                    "Gemini LLM stream completed | model=%s duration_ms=%.2f",
                    self.model_name,
                    duration_ms,
                )
                return
            except Exception as e:
                self.logger.warning("Gemini API key failed during stream (%s). Trying next key...", e)
                last_exception = e

        if last_exception:
            raise last_exception

    def generate_structured_output(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature

        def _call(api_key: str):
            start_time = time.perf_counter()
            response = litellm.completion(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                response_format=response_schema,
                api_key=api_key,
            )
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            usage = getattr(response, "usage", None)
            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

            self.logger.info(
                "Gemini LLM structured call completed | model=%s schema=%s duration_ms=%.2f prompt_tokens=%d completion_tokens=%d total_tokens=%d",
                self.model_name,
                response_schema.__name__,
                duration_ms,
                prompt_tokens,
                completion_tokens,
                total_tokens,
            )
            content = response.choices[0].message.content
            return response_schema.model_validate_json(content)

        return self._execute_with_keys(_call)

    def health_check(self) -> bool:
        return len(self.api_keys) > 0 and self.api_keys[0] != "dummy-key"
