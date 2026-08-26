#!/usr/bin/env python
"""
LLM Backend Validation Harness

Proves the multi-provider layer end to end:

  1. config    — LLM_BACKEND / LLM_FALLBACK_BACKEND resolve and validate.
  2. wiring    — the factory builds the right provider class per backend,
                 with the right protocol and no cross-contamination.
  3. offline   — the fallback decorator routes on availability failures and
                 refuses to route on deterministic ones. Uses fakes, so it
                 runs in CI with no GPU, no network and no API key.
  4. live      — (--live) real health check + real structured extraction
                 against whatever LLM_BACKEND currently points at.

Usage:
    python scripts/check_llm_backend.py              # offline suite only
    python scripts/check_llm_backend.py --live       # + real calls
    python scripts/check_llm_backend.py --backend lightning_vllm --live
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Any, AsyncIterator, Dict, List, Optional, Type

# Import backend.* regardless of the current working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows consoles default to cp1252 and choke on the arrows used below.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pydantic import BaseModel, Field  # noqa: E402

PASSED = 0
FAILED = 0


def check(label: str, condition: bool, detail: str = "") -> bool:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [ OK ] {label}")
    else:
        FAILED += 1
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))
    return condition


def section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


class FeasibilityProbe(BaseModel):
    """Small schema mirroring the shape the real extraction nodes request."""

    project_name: str = Field(description="Name of the project")
    is_feasible: bool = Field(description="Whether the project appears feasible")
    confidence: int = Field(ge=0, le=100, description="Confidence score 0-100")


# ─────────────────────────── Offline fakes ────────────────────────────


class _FakeProvider:
    """Minimal LLMInterface stand-in with scripted success or failure."""

    def __init__(self, name: str, error: Optional[Exception] = None, chunks: int = 0):
        self.model_name = name
        self.last_model_used: Optional[str] = None
        self.error = error
        self.chunks = chunks
        self.calls = 0

    def _serve(self) -> None:
        self.calls += 1
        if self.error:
            raise self.error
        self.last_model_used = self.model_name

    async def generate_text(self, **_: Any) -> str:
        self._serve()
        return f"text from {self.model_name}"

    async def generate_structured_output(
        self, response_schema: Type[BaseModel], **_: Any
    ) -> BaseModel:
        self._serve()
        return response_schema(project_name=self.model_name, is_feasible=True, confidence=90)

    async def generate_text_stream(self, **_: Any) -> AsyncIterator[Dict[str, str]]:
        self.calls += 1
        # Emit `chunks` tokens, then fail — models a mid-stream disconnect.
        for i in range(self.chunks):
            yield {"type": "token", "content": f"c{i}"}
        if self.error:
            raise self.error
        self.last_model_used = self.model_name
        yield {"type": "token", "content": f"text from {self.model_name}"}

    async def generate_structured_output_stream(
        self, response_schema: Type[BaseModel], **_: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        self.calls += 1
        for i in range(self.chunks):
            yield {"type": "thinking", "content": f"t{i}"}
        if self.error:
            raise self.error
        self.last_model_used = self.model_name
        yield {
            "type": "result",
            "data": response_schema(
                project_name=self.model_name, is_feasible=True, confidence=90
            ),
        }

    def health_check(self) -> bool:
        return self.error is None


async def _drain(iterator: AsyncIterator[Any]) -> List[Any]:
    return [item async for item in iterator]


# ──────────────────────────── Test suites ─────────────────────────────


def test_config(requested_backend: Optional[str]) -> None:
    from backend import config

    section("1. CONFIGURATION")
    print(f"  LLM_BACKEND          = {config.LLM_BACKEND}")
    print(f"  LLM_FALLBACK_BACKEND = {config.LLM_FALLBACK_BACKEND}")

    problems = config.validate_llm_config()
    if problems:
        print("\n  Configuration problems reported:")
        for p in problems:
            print(f"    - {p}")

    check(
        "LLM_BACKEND is a supported value",
        config.LLM_BACKEND in config.SUPPORTED_LLM_BACKENDS,
        f"got '{config.LLM_BACKEND}'",
    )
    check("validate_llm_config() reports no problems", not problems)

    if requested_backend:
        check(
            f"--backend override applied ({requested_backend})",
            config.LLM_BACKEND == requested_backend,
        )


def test_wiring() -> None:
    from backend import config
    from backend.LLM.LLMProviderFactory import LLMProviderFactory
    from backend.LLM.providers.fallback_provider import FallbackLLMProvider
    from backend.LLM.providers.GeminiProvider import GeminiProvider
    from backend.LLM.providers.LocalLLM import LocalLLMProvider
    from backend.LLM.providers.openai_compat_provider import OpenAICompatProvider
    from backend.LLM.providers.openai_provider import OpenAIProvider

    section("2. FACTORY WIRING (Strategy + Factory)")

    expected = {
        config.BACKEND_OLLAMA_LOCAL: LocalLLMProvider,
        config.BACKEND_LIGHTNING_VLLM: OpenAICompatProvider,
        config.BACKEND_GEMINI_CLOUD: GeminiProvider,
        config.BACKEND_OPENAI_CLOUD: OpenAIProvider,
    }
    for backend, cls in expected.items():
        try:
            provider = LLMProviderFactory.build_backend(backend, temperature=0.0)
            check(
                f"{backend:<16} builds {cls.__name__}",
                isinstance(provider, cls),
                f"got {type(provider).__name__}",
            )
        except Exception as exc:
            # ollama_local legitimately refuses a /v1 URL; that guard is itself
            # verified below, so surface it rather than counting a hard failure.
            check(f"{backend:<16} builds {cls.__name__}", False, str(exc))

    check(
        "unknown backend raises ValueError",
        _raises(lambda: LLMProviderFactory.build_backend("does_not_exist"), ValueError),
    )

    section("3. PROTOCOL ISOLATION (the bug this refactor targets)")
    check(
        "LocalLLMProvider rejects an OpenAI-tagged model id",
        _raises(
            lambda: LocalLLMProvider(model_name="openai/Qwen/Qwen2.5-14B-Instruct-AWQ"),
            ValueError,
        ),
        "it would have been re-prefixed to 'ollama/openai/...'",
    )
    check(
        "LocalLLMProvider rejects a /v1 base URL",
        _raises(
            lambda: LocalLLMProvider(model_name="qwen3:8b", api_base="https://x.ai/v1"),
            ValueError,
        ),
        "native /api/chat cannot be served from the OpenAI surface",
    )

    vllm = OpenAICompatProvider(
        model_name="Qwen/Qwen2.5-14B-Instruct-AWQ",
        api_base="https://studio.litng.ai/v1",
        api_key="tok",
    )
    check(
        "OpenAICompatProvider preserves slashes in the served model id",
        vllm.served_model_name == "Qwen/Qwen2.5-14B-Instruct-AWQ",
        vllm.served_model_name,
    )
    check(
        "OpenAICompatProvider emits guided_json for structured output",
        "guided_json" in vllm._structured_kwargs(FeasibilityProbe).get("extra_body", {}),
    )
    vllm.use_guided_json = False
    check(
        "OpenAICompatProvider degrades to json_object mode",
        vllm._structured_kwargs(FeasibilityProbe).get("response_format")
        == {"type": "json_object"},
    )

    default = LLMProviderFactory.get_provider(temperature=0.0)
    check(
        "default get_provider() returns the fallback decorator",
        isinstance(default, FallbackLLMProvider),
        type(default).__name__,
    )


def _raises(fn, exc_type) -> bool:
    try:
        fn()
    except exc_type:
        return True
    except Exception:
        return False
    return False


async def test_fallback_offline() -> None:
    import httpx
    import litellm
    from pydantic import ValidationError

    from backend.LLM.errors import is_retryable
    from backend.LLM.providers.fallback_provider import FallbackLLMProvider

    section("4. ERROR CLASSIFICATION")

    timeout = httpx.ConnectError("GPU studio asleep")
    server_err = _http_error(503, "Service Unavailable")
    bad_request = _http_error(400, "context length exceeded")
    schema_err = ValidationError.from_exception_data("FeasibilityProbe", [])

    check("connection error is retryable", is_retryable(timeout))
    check("HTTP 503 is retryable", is_retryable(server_err))
    check("HTTP 404 (endpoint/model not found on primary) is retryable", is_retryable(_http_error(404, "Not Found")))
    check("HTTP 400 is NOT retryable", not is_retryable(bad_request))
    check("Pydantic ValidationError is NOT retryable", not is_retryable(schema_err))
    check("JSON decode error is NOT retryable", not is_retryable(ValueError("bad json")))
    check(
        "rate limit is retryable",
        is_retryable(litellm.RateLimitError("429", llm_provider="vllm", model="q")),
    )

    section("5. FALLBACK ROUTING (Decorator / Chain of Responsibility)")

    # Availability failure → route to the secondary provider.
    primary = _FakeProvider("vllm-primary", error=timeout)
    secondary = _FakeProvider("gemini-fallback")
    wrapper = FallbackLLMProvider(primary, secondary)

    text = await wrapper.generate_text(prompt="hi")
    check("GPU down → generate_text served by fallback", text == "text from gemini-fallback")
    check("last_model_used reports the real server", wrapper.last_model_used == "gemini-fallback")

    result = await wrapper.generate_structured_output(
        prompt="hi", response_schema=FeasibilityProbe
    )
    check(
        "GPU down → structured output served by fallback",
        isinstance(result, FeasibilityProbe) and result.project_name == "gemini-fallback",
    )

    # Deterministic failure → must NOT waste a second provider call.
    primary = _FakeProvider("vllm-primary", error=bad_request)
    secondary = _FakeProvider("gemini-fallback")
    wrapper = FallbackLLMProvider(primary, secondary)
    raised = False
    try:
        await wrapper.generate_text(prompt="hi")
    except Exception:
        raised = True
    check("HTTP 400 propagates instead of falling back", raised)
    check("secondary provider was never called on a 400", secondary.calls == 0)

    # No fallback configured → the original error surfaces.
    solo = FallbackLLMProvider(_FakeProvider("only", error=timeout), None)
    raised = False
    try:
        await solo.generate_text(prompt="hi")
    except Exception:
        raised = True
    check("no fallback configured → error propagates", raised)

    section("6. STREAM INTEGRITY")

    # Failure before the first token → safe to restart on the fallback.
    primary = _FakeProvider("vllm-primary", error=timeout, chunks=0)
    secondary = _FakeProvider("gemini-fallback")
    wrapper = FallbackLLMProvider(primary, secondary)
    chunks = await _drain(wrapper.generate_text_stream(prompt="hi"))
    check(
        "stream failing before any token falls back cleanly",
        chunks == [{"type": "token", "content": "text from gemini-fallback"}],
        str(chunks),
    )

    # Failure after tokens were emitted → restarting would splice two answers.
    primary = _FakeProvider("vllm-primary", error=timeout, chunks=3)
    secondary = _FakeProvider("gemini-fallback")
    wrapper = FallbackLLMProvider(primary, secondary)
    emitted, raised = [], False
    try:
        async for chunk in wrapper.generate_text_stream(prompt="hi"):
            emitted.append(chunk)
    except Exception:
        raised = True
    check("mid-stream failure raises instead of splicing", raised)
    check("mid-stream failure does not call the fallback", secondary.calls == 0)
    check("tokens emitted before the failure are preserved", len(emitted) == 3)

    section("7. THINK-TAG STREAM SPLITTER")
    from backend.LLM.providers.openai_compat_provider import _ThinkTagSplitter

    # Feed one character at a time: the worst-case chunk boundary.
    splitter = _ThinkTagSplitter()
    events: List[Dict[str, str]] = []
    for ch in "A<think>reasoning</think>B":
        events.extend(splitter.feed(ch))
    events.extend(splitter.flush())

    thinking = "".join(e["content"] for e in events if e["type"] == "thinking")
    tokens = "".join(e["content"] for e in events if e["type"] == "token")
    check("tag split across chunks: thinking captured", thinking == "reasoning", thinking)
    check("tag split across chunks: content captured", tokens == "AB", tokens)


def _http_error(status: int, message: str) -> Exception:
    exc = Exception(message)
    exc.status_code = status  # type: ignore[attr-defined]
    return exc


async def test_live() -> None:
    from backend import config
    from backend.services.llm import get_structured_llm

    section("8. LIVE CALL")
    print(f"  Target backend: {config.LLM_BACKEND}")

    provider = get_structured_llm()
    healthy = provider.health_check()
    check(f"health_check() on {config.LLM_BACKEND}", healthy, "endpoint unreachable")

    try:
        result = await provider.generate_structured_output(
            prompt=(
                "Project 'Atlas': migrate 12 TB of ERP data to BigQuery. "
                "Budget approved, team of 4, 6-month deadline. "
                "Assess feasibility."
            ),
            response_schema=FeasibilityProbe,
            system_prompt="You are a senior AI feasibility analyst.",
        )
        check(
            "structured extraction returns a validated model",
            isinstance(result, FeasibilityProbe),
        )
        print(f"         served by : {getattr(provider, 'last_model_used', '?')}")
        print(f"         payload   : {result.model_dump()}")
    except Exception as exc:
        check("structured extraction returns a validated model", False, f"{type(exc).__name__}: {exc}")


async def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the LLM provider layer.")
    parser.add_argument("--backend", help="Override LLM_BACKEND for this run")
    parser.add_argument("--fallback", help="Override LLM_FALLBACK_BACKEND for this run")
    parser.add_argument("--live", action="store_true", help="Perform real network calls")
    args = parser.parse_args()

    # Env must be set before backend.config is imported, since it reads at import time.
    if args.backend:
        os.environ["LLM_BACKEND"] = args.backend
    if args.fallback:
        os.environ["LLM_FALLBACK_BACKEND"] = args.fallback

    test_config(args.backend)
    test_wiring()
    await test_fallback_offline()
    if args.live:
        await test_live()
    else:
        print("\n  (skipping live calls — pass --live to hit the configured backend)")

    section("SUMMARY")
    print(f"  passed: {PASSED}    failed: {FAILED}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
