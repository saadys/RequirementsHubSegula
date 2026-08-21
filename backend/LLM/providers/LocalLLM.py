"""
Local LLM Provider (Ollama)

Concrete provider for local LLM models (e.g. qwen2.5:7b-instruct) via Ollama and LiteLLM.
"""

import json
import re
import time
import urllib.request
from typing import Any, Dict, Iterator, List, Optional, Type
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
        start_time = time.perf_counter()
        raw_model = self.model_name.replace("ollama/", "")

        # Try native Ollama chat streaming for direct thinking tag access
        try:
            req_data: Dict[str, Any] = {
                "model": raw_model,
                "messages": messages,
                "stream": True,
                "options": {"temperature": temp},
            }
            if max_output_tokens:
                req_data["options"]["num_predict"] = max_output_tokens

            req = urllib.request.Request(
                f"{self.api_base}/api/chat",
                data=json.dumps(req_data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            if self.api_key:
                req.add_header("Authorization", f"Bearer {self.api_key}")

            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    if not line.strip():
                        continue
                    chunk = json.loads(line.decode("utf-8"))
                    msg = chunk.get("message", {})
                    t = msg.get("thinking", "")
                    c = msg.get("content", "")
                    if t:
                        yield {"type": "thinking", "content": t}
                    if c:
                        yield {"type": "token", "content": c}

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.logger.info(
                "Local LLM native text stream completed | model=%s duration_ms=%.2f",
                self.model_name,
                duration_ms,
            )
            return
        except Exception as e:
            self.logger.warning("Native Ollama text stream failed (%s); falling back to litellm", str(e))

        response = litellm.completion(
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

        for chunk in response:
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
            "Local LLM stream completed | model=%s duration_ms=%.2f",
            self.model_name,
            duration_ms,
        )

    def _clean_json_string(self, content: str) -> str:
        content = content.strip()
        # Strip thinking tags first
        content = re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.IGNORECASE).strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return content

    def generate_structured_output_stream(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> Iterator[Dict[str, Any]]:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature
        start_time = time.perf_counter()
        raw_model = self.model_name.replace("ollama/", "")
        json_accumulated = ""

        # Try native Ollama chat streaming for step-by-step thinking tokens
        try:
            schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
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
            req = urllib.request.Request(
                f"{self.api_base}/api/chat",
                data=json.dumps(req_data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            if self.api_key:
                req.add_header("Authorization", f"Bearer {self.api_key}")

            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    if not line.strip():
                        continue
                    chunk = json.loads(line.decode("utf-8"))
                    msg = chunk.get("message", {})
                    t = msg.get("thinking", "")
                    c = msg.get("content", "")
                    if t:
                        yield {"type": "thinking", "content": t}
                    if c:
                        json_accumulated += c

        except Exception as e:
            self.logger.warning(
                "Native Ollama structured stream failed (%s); falling back to litellm",
                str(e),
            )
            schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
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

            response = litellm.completion(
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

            for chunk in response:
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
            "Local LLM structured stream completed | model=%s schema=%s duration_ms=%.2f",
            self.model_name,
            response_schema.__name__,
            duration_ms,
        )

        clean_content = self._clean_json_string(json_accumulated)
        validated_result = None
        try:
            validated_result = response_schema.model_validate_json(clean_content)
        except Exception:
            # Fallback: parse into dict and validate
            parsed_dict = json.loads(clean_content)
            if isinstance(parsed_dict, dict):
                if response_schema.__name__ not in parsed_dict and len(parsed_dict) == 1:
                    first_val = next(iter(parsed_dict.values()))
                    if isinstance(first_val, dict):
                        try:
                            validated_result = response_schema.model_validate(first_val)
                        except Exception:
                            pass
                if validated_result is None:
                    validated_result = response_schema.model_validate(parsed_dict)
            else:
                raise

        yield {"type": "result", "data": validated_result}

    def generate_structured_output(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        res = None
        for chunk in self.generate_structured_output_stream(
            prompt=prompt,
            response_schema=response_schema,
            system_prompt=system_prompt,
            temperature=temperature,
        ):
            if chunk.get("type") == "result":
                res = chunk.get("data")
        if res is None:
            raise ValueError(f"Failed to produce structured output for {response_schema.__name__}")
        return res

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
