"""
Local LLM Provider (Ollama)

Concrete provider for local LLM models (e.g. qwen2.5:7b-instruct) via Ollama and LiteLLM.
"""

import json
import re
import time
import urllib.request
from typing import Any, AsyncIterator, Dict, List, Optional, Type
import httpx
import litellm

from backend import config
from backend.LLM.providers.base_provider import BaseLLMProvider
from backend.LLM.LLMInterfaces import T


class LocalLLMProvider(BaseLLMProvider):
    """Native Ollama provider supporting text generation and Pydantic structured output.

    Speaks the *native* Ollama protocol (/api/chat, /api/tags). For an
    OpenAI-compatible server (vLLM on Lightning AI, TGI, LM Studio) use
    OpenAICompatProvider instead: the two wire formats are not interchangeable.
    """

    def __init__(
        self,
        model_name: str = "ollama/qwen3:8b",
        temperature: float = 0.0,
        api_base: Optional[str] = None,
    ):
        # A model id already tagged for another litellm stack (openai/, gemini/)
        # must not be re-prefixed into a nonsense route like "ollama/openai/...".
        if "/" in model_name and not model_name.startswith("ollama/"):
            raise ValueError(
                f"LocalLLMProvider speaks the native Ollama protocol but received "
                f"model_name='{model_name}'. Use a bare Ollama tag (e.g. 'qwen3:8b'), "
                f"or route this model to OpenAICompatProvider "
                f"(LLM_BACKEND=lightning_vllm)."
            )
        clean_model = model_name if model_name.startswith("ollama/") else f"ollama/{model_name}"
        super().__init__(model_name=clean_model, temperature=temperature)

        base = api_base or getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434")
        if base.rstrip("/").endswith("/v1"):
            raise ValueError(
                f"OLLAMA_BASE_URL='{base}' points at the OpenAI-compatible surface "
                f"(/v1), which this provider does not speak. Set "
                f"LLM_BACKEND=lightning_vllm for that endpoint, or drop the '/v1' "
                f"suffix to use the native Ollama API."
            )
        self.api_base = base
        self.api_key = getattr(config, "OLLAMA_API_KEY", "")

    def _get_extra_headers(self) -> Optional[Dict[str, str]]:
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return None

    async def generate_text(
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
        response = await litellm.acompletion(
            model=self.model_name,
            messages=messages,
            temperature=temp,
            max_tokens=max_output_tokens,
            api_base=self.api_base,
            extra_headers=self._get_extra_headers(),
            timeout=60,
            num_retries=config.LLM_MAX_RETRIES,
            retry_strategy="exponential_backoff_retry",
            retry_after=config.LLM_RETRY_BASE_DELAY_SECONDS,
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
        self.last_model_used = self.model_name
        raw_content = response.choices[0].message.content
        # Strip thinking tags if present in text generation
        return re.sub(r"<think>[\s\S]*?</think>", "", raw_content, flags=re.IGNORECASE).strip()

    async def generate_text_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        max_output_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, str]]:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature
        start_time = time.perf_counter()
        raw_model = self.model_name.replace("ollama/", "")

        # 1. Try native Ollama async streaming for direct thinking/content separation
        try:
            req_data: Dict[str, Any] = {
                "model": raw_model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temp},
            }
            if max_output_tokens:
                req_data["options"]["num_predict"] = max_output_tokens

            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", f"{self.api_base.rstrip('/')}/api/chat", json=req_data, headers=headers) as resp:
                    if resp.status_code == 200:
                        async for line in resp.aiter_lines():
                            if not line.strip():
                                continue
                            chunk = json.loads(line)
                            msg = chunk.get("message", {})
                            t = msg.get("thinking", "")
                            c = msg.get("content", "")
                            if t:
                                yield {"type": "thinking", "content": t}
                            if c:
                                yield {"type": "token", "content": c}

                        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                        self.logger.info(
                            "Local LLM native async stream completed | model=%s duration_ms=%.2f",
                            self.model_name,
                            duration_ms,
                        )
                        self.last_model_used = self.model_name
                        return
        except Exception as e:
            self.logger.warning("Native Ollama async text stream failed (%s); falling back to litellm", str(e))

        # 2. Fallback: litellm async streaming with think tags parsing
        response = await litellm.acompletion(
            model=self.model_name,
            messages=messages,
            temperature=temp,
            max_tokens=max_output_tokens,
            api_base=self.api_base,
            extra_headers=self._get_extra_headers(),
            stream=True,
            timeout=120,
        )

        in_thinking = False
        buffer = ""

        async for chunk in response:
            if not chunk.choices or not chunk.choices[0].delta:
                continue

            delta = chunk.choices[0].delta
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                yield {"type": "thinking", "content": reasoning}

            content = getattr(delta, "content", "") or ""
            if not content:
                continue

            buffer += content

            while buffer:
                if not in_thinking:
                    if "<think>" in buffer:
                        pre_think, _, post_think = buffer.partition("<think>")
                        if pre_think:
                            yield {"type": "token", "content": pre_think}
                        in_thinking = True
                        buffer = post_think
                    elif "<" in buffer:
                        tag_idx = buffer.find("<")
                        potential = buffer[tag_idx:]
                        if "<think>".startswith(potential):
                            if tag_idx > 0:
                                yield {"type": "token", "content": buffer[:tag_idx]}
                                buffer = potential
                            break
                        else:
                            yield {"type": "token", "content": buffer[:tag_idx + 1]}
                            buffer = buffer[tag_idx + 1:]
                    else:
                        yield {"type": "token", "content": buffer}
                        buffer = ""
                else:
                    if "</think>" in buffer:
                        think_text, _, post_think = buffer.partition("</think>")
                        if think_text:
                            yield {"type": "thinking", "content": think_text}
                        in_thinking = False
                        buffer = post_think.lstrip("\n")
                    elif "<" in buffer:
                        tag_idx = buffer.find("<")
                        potential = buffer[tag_idx:]
                        if "</think>".startswith(potential):
                            if tag_idx > 0:
                                yield {"type": "thinking", "content": buffer[:tag_idx]}
                                buffer = potential
                            break
                        else:
                            yield {"type": "thinking", "content": buffer[:tag_idx + 1]}
                            buffer = buffer[tag_idx + 1:]
                    else:
                        yield {"type": "thinking", "content": buffer}
                        buffer = ""

        if buffer:
            event_type = "thinking" if in_thinking else "token"
            yield {"type": event_type, "content": buffer}

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        self.logger.info(
            "Local LLM litellm stream completed | model=%s duration_ms=%.2f",
            self.model_name,
            duration_ms,
        )
        self.last_model_used = self.model_name

    def _clean_json_string(self, content: str) -> str:
        content = content.strip()
        # Strip thinking tags first
        content = re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.IGNORECASE).strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return content

    def _validate_schema_content(self, clean_content: str, response_schema: Type[T]) -> T:
        """Validates JSON content against Pydantic schema with fallback dictionary unpacking."""
        try:
            return response_schema.model_validate_json(clean_content)
        except Exception:
            parsed_dict = json.loads(clean_content)
            if isinstance(parsed_dict, dict):
                if response_schema.__name__ not in parsed_dict and len(parsed_dict) == 1:
                    first_val = next(iter(parsed_dict.values()))
                    if isinstance(first_val, dict):
                        try:
                            return response_schema.model_validate(first_val)
                        except Exception:
                            pass
                return response_schema.model_validate(parsed_dict)
            raise

    async def generate_structured_output_stream(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature
        start_time = time.perf_counter()
        raw_model = self.model_name.replace("ollama/", "")
        json_accumulated = ""
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)

        # 1. Try native Ollama async streaming for step-by-step thinking tokens + JSON format
        try:
            json_instruction = (
                f"\n\nCRITICAL INSTRUCTION:\n"
                f"You MUST output the final result strictly as a valid JSON object matching this schema:\n"
                f"{schema_json}\n"
            )
            native_messages = [dict(m) for m in messages]
            if native_messages and native_messages[-1]["role"] == "user":
                native_messages[-1] = {
                    "role": "user",
                    "content": native_messages[-1]["content"] + json_instruction,
                }
            else:
                native_messages.append({"role": "user", "content": json_instruction})

            req_data: Dict[str, Any] = {
                "model": raw_model,
                "messages": native_messages,
                "stream": True,
                "format": "json",
                "options": {"temperature": temp},
            }
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", f"{self.api_base.rstrip('/')}/api/chat", json=req_data, headers=headers) as resp:
                    if resp.status_code == 200:
                        async for line in resp.aiter_lines():
                            if not line.strip():
                                continue
                            chunk = json.loads(line)
                            msg = chunk.get("message", {})
                            t = msg.get("thinking", "")
                            c = msg.get("content", "")
                            if t:
                                yield {"type": "thinking", "content": t}
                            if c:
                                json_accumulated += c

                        clean_content = self._clean_json_string(json_accumulated)
                        validated_result = self._validate_schema_content(clean_content, response_schema)
                        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                        self.logger.info(
                            "Local LLM native structured async stream completed | model=%s schema=%s duration_ms=%.2f",
                            self.model_name,
                            response_schema.__name__,
                            duration_ms,
                        )
                        self.last_model_used = self.model_name
                        yield {"type": "result", "data": validated_result}
                        return
        except Exception as e:
            self.logger.warning(
                "Native Ollama structured async stream failed (%s); falling back to litellm",
                str(e),
            )

        # 2. Fallback: litellm streaming with <think> tag extraction and JSON accumulation
        json_instruction = (
            f"\n\nCRITICAL INSTRUCTION:\n"
            f"1. First, provide your thorough step-by-step analytical reasoning inside <think>...</think> tags.\n"
            f"2. Immediately after </think>, output the final result strictly as a valid JSON object matching this schema:\n"
            f"{schema_json}\nDo not include any text outside the <think> tags and the JSON object."
        )
        fb_messages = list(messages)
        if fb_messages and fb_messages[-1]["role"] == "user":
            fb_messages[-1] = {"role": "user", "content": fb_messages[-1]["content"] + json_instruction}
        else:
            fb_messages.append({"role": "user", "content": json_instruction})

        response = await litellm.acompletion(
            model=self.model_name,
            messages=fb_messages,
            temperature=temp,
            api_base=self.api_base,
            extra_headers=self._get_extra_headers(),
            stream=True,
            timeout=90,
        )

        in_thinking = False
        buffer = ""
        json_accumulated = ""

        async for chunk in response:
            if not chunk.choices or not chunk.choices[0].delta:
                continue
            delta = getattr(chunk.choices[0].delta, "content", "") or ""
            if not delta:
                continue

            buffer += delta

            while buffer:
                if not in_thinking:
                    if "<think>" in buffer:
                        before, _, after = buffer.partition("<think>")
                        if before:
                            json_accumulated += before
                        in_thinking = True
                        buffer = after
                    elif "<" in buffer:
                        tag_idx = buffer.find("<")
                        potential = buffer[tag_idx:]
                        if "<think>".startswith(potential):
                            if tag_idx > 0:
                                json_accumulated += buffer[:tag_idx]
                                buffer = potential
                            break
                        else:
                            json_accumulated += buffer[:tag_idx + 1]
                            buffer = buffer[tag_idx + 1:]
                    else:
                        json_accumulated += buffer
                        buffer = ""
                else:
                    if "</think>" in buffer:
                        think_text, _, after = buffer.partition("</think>")
                        if think_text:
                            yield {"type": "thinking", "content": think_text}
                        in_thinking = False
                        buffer = after
                    elif "<" in buffer:
                        tag_idx = buffer.find("<")
                        potential = buffer[tag_idx:]
                        if "</think>".startswith(potential):
                            if tag_idx > 0:
                                yield {"type": "thinking", "content": buffer[:tag_idx]}
                                buffer = potential
                            break
                        else:
                            yield {"type": "thinking", "content": buffer[:tag_idx + 1]}
                            buffer = buffer[tag_idx + 1:]
                    else:
                        yield {"type": "thinking", "content": buffer}
                        buffer = ""

        if buffer:
            if in_thinking:
                yield {"type": "thinking", "content": buffer}
            else:
                json_accumulated += buffer

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        self.logger.info(
            "Local LLM structured litellm stream completed | model=%s schema=%s duration_ms=%.2f",
            self.model_name,
            response_schema.__name__,
            duration_ms,
        )

        clean_content = self._clean_json_string(json_accumulated)
        validated_result = self._validate_schema_content(clean_content, response_schema)
        self.last_model_used = self.model_name
        yield {"type": "result", "data": validated_result}

    async def generate_structured_output(
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

        # A 7B local model occasionally emits malformed JSON even under
        # json_object mode. litellm's num_retries only covers transport-level
        # failures (the HTTP call itself succeeds here), so invalid/incomplete
        # JSON is retried explicitly, distinct from FallbackLLMProvider's
        # cross-provider fallback which only triggers once all attempts here
        # are exhausted.
        last_error: Exception | None = None
        for attempt in range(config.LLM_MAX_RETRIES + 1):
            start_time = time.perf_counter()
            response = await litellm.acompletion(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                api_base=self.api_base,
                extra_headers=self._get_extra_headers(),
                response_format={"type": "json_object"},
                num_retries=config.LLM_MAX_RETRIES,
                retry_strategy="exponential_backoff_retry",
                retry_after=config.LLM_RETRY_BASE_DELAY_SECONDS,
            )
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            usage = getattr(response, "usage", None)
            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

            self.logger.info(
                "Local LLM structured call completed | model=%s schema=%s attempt=%d duration_ms=%.2f prompt_tokens=%d completion_tokens=%d total_tokens=%d",
                self.model_name,
                response_schema.__name__,
                attempt + 1,
                duration_ms,
                prompt_tokens,
                completion_tokens,
                total_tokens,
            )

            raw_content = response.choices[0].message.content
            clean_content = self._clean_json_string(raw_content)
            try:
                result = self._validate_schema_content(clean_content, response_schema)
                self.last_model_used = self.model_name
                return result
            except Exception as e:
                last_error = e
                self.logger.warning(
                    "Local LLM returned invalid JSON for schema=%s (attempt %d/%d): %s",
                    response_schema.__name__,
                    attempt + 1,
                    config.LLM_MAX_RETRIES + 1,
                    e,
                )

        assert last_error is not None
        raise last_error

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
