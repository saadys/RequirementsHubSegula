"""
Local LLM Provider (Ollama)

Concrete provider for local LLM models (e.g. qwen2.5:7b-instruct) via Ollama and LiteLLM.
"""

import json
import re
import urllib.request
from typing import Dict, List, Optional, Type
import litellm

from backend import config
from backend.LLM.providers.base_provider import BaseLLMProvider
from backend.LLM.LLMInterfaces import T


class LocalLLMProvider(BaseLLMProvider):
    """Local Ollama Provider supporting text generation and Pydantic structured output."""

    def __init__(
        self,
        model_name: str = "ollama/qwen2.5:7b-instruct",
        temperature: float = 0.0,
        api_base: Optional[str] = None,
    ):
        clean_model = model_name if model_name.startswith("ollama/") else f"ollama/{model_name}"
        super().__init__(model_name=clean_model, temperature=temperature)
        self.api_base = api_base or getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434")

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
            api_base=self.api_base,
        )
        return response.choices[0].message.content

    def _clean_json_string(self, content: str) -> str:
        content = content.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return content

    def generate_structured_output(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature

        # Inject JSON schema instruction to enforce strict structure for 7B local models
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        json_instruction = (
            f"\n\nIMPORTANT: You MUST respond ONLY with a valid JSON object matching this JSON Schema:\n"
            f"{schema_json}\nDo not include any markdown wrapper or explanation outside the JSON."
        )

        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += json_instruction
        else:
            messages.append({"role": "user", "content": json_instruction})

        response = litellm.completion(
            model=self.model_name,
            messages=messages,
            temperature=temp,
            api_base=self.api_base,
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content
        clean_content = self._clean_json_string(raw_content)
        return response_schema.model_validate_json(clean_content)

    def health_check(self) -> bool:
        try:
            url = f"{self.api_base.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception as e:
            self.logger.warning(f"LocalLLM health check failed for {self.api_base}: {e}")
            return False
