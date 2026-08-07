"""
Gemini LLM Provider

Concrete provider for Google Gemini models with multi-key round robin and Pydantic structured output.
"""

from typing import Dict, List, Optional, Type
from pydantic import BaseModel
import litellm

from backend import config
from backend.LLM.providers.base_provider import BaseLLMProvider
from backend.LLM.LLMInterfaces import T


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider with multi-key failover and structured output."""

    def __init__(self, model_name: str = "gemini/gemini-1.5-flash", temperature: float = 0.0):
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
                self.logger.warning(f"Gemini API key failed: {e}. Trying next key...")
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
            response = litellm.completion(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                max_tokens=max_output_tokens,
                api_key=api_key,
            )
            return response.choices[0].message.content

        return self._execute_with_keys(_call)

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
            response = litellm.completion(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                response_format=response_schema,
                api_key=api_key,
            )
            content = response.choices[0].message.content
            # Parse json into pydantic model
            return response_schema.model_validate_json(content)

        return self._execute_with_keys(_call)

    def health_check(self) -> bool:
        return len(self.api_keys) > 0 and self.api_keys[0] != "dummy-key"
