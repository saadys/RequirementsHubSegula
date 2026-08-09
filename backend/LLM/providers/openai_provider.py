"""
OpenAI LLM Provider

Concrete provider for OpenAI models (GPT-4o, GPT-4o-mini) with Pydantic structured output.
"""

from typing import Dict, List, Optional, Type
import litellm

from backend import config
from backend.LLM.providers.base_provider import BaseLLMProvider
from backend.LLM.LLMInterfaces import T


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider supporting text generation and Pydantic structured outputs."""

    def __init__(self, model_name: str = "openai/gpt-4o", temperature: float = 0.0):
        clean_model = model_name if model_name.startswith("openai/") else f"openai/{model_name}"
        super().__init__(model_name=clean_model, temperature=temperature)
        self.api_key = config.OPENAI_API_KEY

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

        response = litellm.completion(
            model=self.model_name,
            messages=messages,
            temperature=temp,
            max_tokens=max_output_tokens,
            api_key=self.api_key,
        )
        return response.choices[0].message.content

    def generate_structured_output(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature

        response = litellm.completion(
            model=self.model_name,
            messages=messages,
            temperature=temp,
            response_format=response_schema,
            api_key=self.api_key,
        )
        content = response.choices[0].message.content
        return response_schema.model_validate_json(content)

    def health_check(self) -> bool:
        return bool(self.api_key)
