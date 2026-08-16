"""
Local LLM Provider (Ollama)

Concrete provider for local LLM models (e.g. qwen2.5:7b-instruct) via Ollama and LiteLLM.
"""

import json
import re
import time
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
        model_name: str = "ollama/qwen3:8b",
        temperature: float = 0.0,
        api_base: Optional[str] = None,
    ):
        clean_model = model_name if model_name.startswith("ollama/") else f"ollama/{model_name}"
        super().__init__(model_name=clean_model, temperature=temperature)
        self.api_base = api_base or getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.api_key = getattr(config, "OLLAMA_API_KEY", "")

    def _get_extra_headers(self) -> Optional[Dict[str, str]]:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return None

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

        start_time = time.perf_counter()
        response = litellm.completion(
            model=self.model_name,
            messages=messages,
            temperature=temp,
            max_tokens=max_output_tokens,
            api_base=self.api_base,
            extra_headers=self._get_extra_headers(),
            timeout=60,
        )
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

        self.logger.info(
            "Local LLM text call completed | model=%s duration_ms=%.2f prompt_tokens=%d completion_tokens=%d total_tokens=%d",
            self.model_name,
            duration_ms,
            prompt_tokens,
            completion_tokens,
            total_tokens,
        )
        raw_content = response.choices[0].message.content
        # Strip thinking tags if present in text generation
        return re.sub(r"<think>[\s\S]*?</think>", "", raw_content, flags=re.IGNORECASE).strip()

    def _clean_json_string(self, content: str) -> str:
        content = content.strip()
        # Strip thinking tags first
        content = re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.IGNORECASE).strip()
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

        # Inject JSON schema instruction to enforce strict structure for local models
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        json_instruction = (
            f"\n\nIMPORTANT: You MUST respond ONLY with a valid JSON object matching this JSON Schema:\n"
            f"{schema_json}\nDo not include any markdown wrapper or explanation outside the JSON."
        )

        if messages and messages[-1]["role"] == "user":
            messages[-1]["content"] += json_instruction
        else:
            messages.append({"role": "user", "content": json_instruction})

        start_time = time.perf_counter()
        response = litellm.completion(
            model=self.model_name,
            messages=messages,
            temperature=temp,
            api_base=self.api_base,
            extra_headers=self._get_extra_headers(),
            response_format={"type": "json_object"},
            timeout=60,
        )
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

        self.logger.info(
            "Local LLM structured call completed | model=%s schema=%s duration_ms=%.2f prompt_tokens=%d completion_tokens=%d total_tokens=%d",
            self.model_name,
            response_schema.__name__,
            duration_ms,
            prompt_tokens,
            completion_tokens,
            total_tokens,
        )

        raw_content = response.choices[0].message.content
        clean_content = self._clean_json_string(raw_content)
        
        try:
            return response_schema.model_validate_json(clean_content)
        except Exception:
            # Fallback: parse into dict and validate
            parsed_dict = json.loads(clean_content)
            if isinstance(parsed_dict, dict):
                # If wrapped under a top-level key like "questions" or "data"
                if response_schema.__name__ not in parsed_dict and len(parsed_dict) == 1:
                    first_val = next(iter(parsed_dict.values()))
                    if isinstance(first_val, dict):
                        try:
                            return response_schema.model_validate(first_val)
                        except Exception:
                            pass
                return response_schema.model_validate(parsed_dict)
            raise

    def health_check(self) -> bool:
        try:
            url = f"{self.api_base.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, method="GET")
            if self.api_key:
                req.add_header("Authorization", f"Bearer {self.api_key}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception as e:
            self.logger.warning("LocalLLM health check failed for %s: %s", self.api_base, e)
            return False
