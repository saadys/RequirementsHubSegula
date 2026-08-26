"""
OpenAI-Compatible LLM Provider

Concrete provider for any server exposing the OpenAI /v1 API surface behind a
base URL and a Bearer token: vLLM (Lightning AI GPU studios), TGI, LM Studio,
llama.cpp server, or a self-hosted gateway.

Deliberately distinct from LocalLLMProvider, which speaks the *native* Ollama
protocol (/api/chat, /api/tags). The two wire formats are not interchangeable:
mixing them in one class is what made the previous vLLM configuration silently
degrade on every call.

Structured output strategy (best effort, degrading gracefully):
  1. `guided_json` - vLLM grammar-constrained decoding (xgrammar / outlines).
     Token-level constraint, so syntactically invalid JSON is unreachable.
  2. `response_format={"type": "json_object"}` - generic JSON mode.
  3. Schema injected in the prompt + explicit re-validation retries.
Callers never see any of this: they get a validated Pydantic model.
"""

import json
import re
import time
import urllib.request
from typing import Any, AsyncIterator, Dict, List, Optional, Type

import litellm

from backend import config
from backend.LLM.LLMInterfaces import T
from backend.LLM.providers.base_provider import BaseLLMProvider


class OpenAICompatProvider(BaseLLMProvider):
    """Provider for OpenAI-compatible inference servers (vLLM, TGI, LM Studio)."""

    def __init__(
        self,
        model_name: str,
        temperature: float = 0.0,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        use_guided_json: Optional[bool] = None,
    ):
        # litellm routes on the `openai/` prefix; the remainder is forwarded to
        # the server verbatim. Model ids legitimately contain slashes
        # (e.g. Qwen/Qwen2.5-14B-Instruct-AWQ), so only the leading tag is added.
        clean_model = model_name if model_name.startswith("openai/") else f"openai/{model_name}"
        super().__init__(model_name=clean_model, temperature=temperature)

        self.api_base = (api_base or config.VLLM_BASE_URL).rstrip("/")
        # litellm requires a non-empty key even for unauthenticated servers.
        self.api_key = api_key or config.VLLM_API_KEY or "not-needed"
        self.timeout = timeout if timeout is not None else config.LLM_REQUEST_TIMEOUT_SECONDS
        self.use_guided_json = (
            use_guided_json if use_guided_json is not None else config.VLLM_USE_GUIDED_JSON
        )

    @property
    def served_model_name(self) -> str:
        """Model id as the remote server knows it (without the litellm prefix)."""
        return self.model_name.removeprefix("openai/")

    def _base_kwargs(self, messages: List[Dict[str, str]], temp: float) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "messages": messages,
            "temperature": temp,
            "api_base": self.api_base,
            "api_key": self.api_key,
            "timeout": self.timeout,
        }

    def _retry_kwargs(self) -> Dict[str, Any]:
        return {
            "num_retries": config.LLM_MAX_RETRIES,
            "retry_strategy": "exponential_backoff_retry",
            "retry_after": config.LLM_RETRY_BASE_DELAY_SECONDS,
        }

    @staticmethod
    def _strip_reasoning(content: str) -> str:
        """Removes <think> blocks emitted by reasoning models (DeepSeek-R1, QwQ)."""
        return re.sub(r"<think>[\s\S]*?</think>", "", content or "", flags=re.IGNORECASE).strip()

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
            **self._base_kwargs(messages, temp),
            max_tokens=max_output_tokens,
            **self._retry_kwargs(),
        )
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        usage = getattr(response, "usage", None)

        self.logger.info(
            "vLLM text call completed | model=%s duration_ms=%.2f prompt_tokens=%d completion_tokens=%d",
            self.model_name,
            duration_ms,
            getattr(usage, "prompt_tokens", 0) if usage else 0,
            getattr(usage, "completion_tokens", 0) if usage else 0,
        )
        self.last_model_used = self.model_name
        return self._strip_reasoning(response.choices[0].message.content)

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

        response = await litellm.acompletion(
            **self._base_kwargs(messages, temp),
            max_tokens=max_output_tokens,
            stream=True,
        )

        splitter = _ThinkTagSplitter()
        async for chunk in response:
            if not chunk.choices or not chunk.choices[0].delta:
                continue
            delta = chunk.choices[0].delta

            # vLLM exposes reasoning separately when started with
            # --reasoning-parser; otherwise it arrives inline as <think> tags.
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                yield {"type": "thinking", "content": reasoning}

            content = getattr(delta, "content", "") or ""
            if content:
                for event in splitter.feed(content):
                    yield event

        for event in splitter.flush():
            yield event

        self.logger.info(
            "vLLM text stream completed | model=%s duration_ms=%.2f",
            self.model_name,
            round((time.perf_counter() - start_time) * 1000, 2),
        )
        self.last_model_used = self.model_name

    def _json_instruction(self, response_schema: Type[T]) -> str:
        schema_json = json.dumps(response_schema.model_json_schema(), indent=2)
        return (
            "\n\nIMPORTANT: You MUST respond ONLY with a valid JSON object matching "
            f"this JSON Schema:\n{schema_json}\n"
            "Do not include markdown fences or any explanation outside the JSON object."
        )

    @staticmethod
    def _with_instruction(
        messages: List[Dict[str, str]], instruction: str
    ) -> List[Dict[str, str]]:
        out = [dict(m) for m in messages]
        if out and out[-1]["role"] == "user":
            out[-1]["content"] += instruction
        else:
            out.append({"role": "user", "content": instruction})
        return out

    @staticmethod
    def _clean_json_string(content: str) -> str:
        content = re.sub(r"<think>[\s\S]*?</think>", "", content or "", flags=re.IGNORECASE).strip()
        fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
        if fenced:
            return fenced.group(1).strip()
        return content

    @staticmethod
    def _validate(clean_content: str, response_schema: Type[T]) -> T:
        """Validates JSON against the schema, unwrapping a single-key envelope.

        Smaller models frequently wrap the payload: {"FactExtraction": {...}}.
        Unwrapping here keeps that quirk out of the calling nodes.
        """
        try:
            return response_schema.model_validate_json(clean_content)
        except Exception:
            parsed = json.loads(clean_content)
            if isinstance(parsed, dict):
                if len(parsed) == 1 and response_schema.__name__ not in parsed:
                    inner = next(iter(parsed.values()))
                    if isinstance(inner, dict):
                        try:
                            return response_schema.model_validate(inner)
                        except Exception:
                            pass
                return response_schema.model_validate(parsed)
            raise

    def _structured_kwargs(self, response_schema: Type[T]) -> Dict[str, Any]:
        """Returns the server-side JSON constraint kwargs for this backend."""
        if self.use_guided_json:
            # vLLM reads guided_json from extra_body; grammar-constrained
            # decoding makes syntactically invalid JSON unreachable.
            return {
                "extra_body": {
                    "guided_json": response_schema.model_json_schema(),
                    "guided_decoding_backend": config.VLLM_GUIDED_BACKEND,
                }
            }
        return {"response_format": {"type": "json_object"}}

    async def generate_structured_output(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> T:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature
        messages = self._with_instruction(messages, self._json_instruction(response_schema))

        constraint_kwargs = self._structured_kwargs(response_schema)
        last_error: Exception | None = None

        # Two distinct failure modes are handled here:
        #   - transport failures -> litellm num_retries (inside each attempt)
        #   - schema violations  -> this loop (the HTTP call itself succeeded)
        # Only once both are exhausted does FallbackLLMProvider take over.
        for attempt in range(config.LLM_MAX_RETRIES + 1):
            start_time = time.perf_counter()
            try:
                response = await litellm.acompletion(
                    **self._base_kwargs(messages, temp),
                    **constraint_kwargs,
                    **self._retry_kwargs(),
                )
            except Exception as exc:
                # A server that rejects guided_json (not vLLM, or an older build)
                # answers 400. Degrade once to plain JSON mode rather than
                # burning the cross-provider fallback on a capability mismatch.
                if constraint_kwargs.get("extra_body") and _is_bad_request(exc):
                    self.logger.warning(
                        "Server rejected guided_json (%s); degrading to json_object mode", exc
                    )
                    self.use_guided_json = False
                    constraint_kwargs = {"response_format": {"type": "json_object"}}
                    last_error = exc
                    continue
                raise

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            usage = getattr(response, "usage", None)
            self.logger.info(
                "vLLM structured call completed | model=%s schema=%s attempt=%d "
                "guided=%s duration_ms=%.2f prompt_tokens=%d completion_tokens=%d",
                self.model_name,
                response_schema.__name__,
                attempt + 1,
                self.use_guided_json,
                duration_ms,
                getattr(usage, "prompt_tokens", 0) if usage else 0,
                getattr(usage, "completion_tokens", 0) if usage else 0,
            )

            clean_content = self._clean_json_string(response.choices[0].message.content)
            try:
                result = self._validate(clean_content, response_schema)
                self.last_model_used = self.model_name
                return result
            except Exception as exc:
                last_error = exc
                self.logger.warning(
                    "vLLM returned invalid JSON for schema=%s (attempt %d/%d): %s",
                    response_schema.__name__,
                    attempt + 1,
                    config.LLM_MAX_RETRIES + 1,
                    exc,
                )

        assert last_error is not None
        raise last_error

    async def generate_structured_output_stream(
        self,
        prompt: str | List[Dict[str, str]],
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        messages = self._format_messages(prompt=prompt, system_prompt=system_prompt)
        temp = temperature if temperature is not None else self.default_temperature
        messages = self._with_instruction(messages, self._json_instruction(response_schema))
        start_time = time.perf_counter()

        response = await litellm.acompletion(
            **self._base_kwargs(messages, temp),
            **self._structured_kwargs(response_schema),
            stream=True,
        )

        splitter = _ThinkTagSplitter()
        json_accumulated = ""

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

            # Thinking is streamed to the client; the JSON body is buffered
            # until complete, since a partial object cannot be validated.
            for event in splitter.feed(content):
                if event["type"] == "thinking":
                    yield event
                else:
                    json_accumulated += event["content"]

        for event in splitter.flush():
            if event["type"] == "thinking":
                yield event
            else:
                json_accumulated += event["content"]

        self.logger.info(
            "vLLM structured stream completed | model=%s schema=%s duration_ms=%.2f",
            self.model_name,
            response_schema.__name__,
            round((time.perf_counter() - start_time) * 1000, 2),
        )

        validated = self._validate(self._clean_json_string(json_accumulated), response_schema)
        self.last_model_used = self.model_name
        yield {"type": "result", "data": validated}

    def health_check(self) -> bool:
        """Probes GET /models - the OpenAI-compatible liveness endpoint."""
        url = f"{self.api_base}/models"
        req = urllib.request.Request(url, method="GET")
        if self.api_key and self.api_key != "not-needed":
            req.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(req, timeout=config.LLM_HEALTHCHECK_TIMEOUT_SECONDS) as resp:
                return resp.status == 200
        except Exception as exc:
            self.logger.warning("vLLM health check failed for %s: %s", url, exc)
            return False


def _is_bad_request(exc: Exception) -> bool:
    """True when the server rejected the request shape (HTTP 400/422)."""
    if getattr(exc, "status_code", None) in (400, 422):
        return True
    bad_request_cls = getattr(litellm, "BadRequestError", None)
    return bad_request_cls is not None and isinstance(exc, bad_request_cls)


class _ThinkTagSplitter:
    """Incremental splitter separating <think>...</think> spans from content.

    Streaming chunks split tag literals arbitrarily ("<thi" | "nk>"), so a
    partial suffix that could still become a tag is held back rather than
    emitted. Replaces the duplicated inline state machines that previously
    lived in both streaming methods of LocalLLMProvider.
    """

    OPEN = "<think>"
    CLOSE = "</think>"

    def __init__(self) -> None:
        self._buffer = ""
        self._in_thinking = False

    def feed(self, content: str) -> List[Dict[str, str]]:
        self._buffer += content
        events: List[Dict[str, str]] = []

        while self._buffer:
            marker = self.CLOSE if self._in_thinking else self.OPEN
            kind = "thinking" if self._in_thinking else "token"

            if marker in self._buffer:
                before, _, after = self._buffer.partition(marker)
                if before:
                    events.append({"type": kind, "content": before})
                self._in_thinking = not self._in_thinking
                self._buffer = after if self._in_thinking else after.lstrip("\n")
                continue

            idx = self._buffer.find("<")
            if idx == -1:
                events.append({"type": kind, "content": self._buffer})
                self._buffer = ""
                break

            suffix = self._buffer[idx:]
            if marker.startswith(suffix):
                # Possibly a truncated tag: emit what precedes it, hold the rest.
                if idx > 0:
                    events.append({"type": kind, "content": self._buffer[:idx]})
                    self._buffer = suffix
                break

            events.append({"type": kind, "content": self._buffer[: idx + 1]})
            self._buffer = self._buffer[idx + 1 :]

        return [e for e in events if e["content"]]

    def flush(self) -> List[Dict[str, str]]:
        if not self._buffer:
            return []
        kind = "thinking" if self._in_thinking else "token"
        event = {"type": kind, "content": self._buffer}
        self._buffer = ""
        return [event]
