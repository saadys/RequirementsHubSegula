"""
Test Multi-Provider Streaming & Fallback Delegation
Explicitly tests:
1. GeminiProvider.generate_text_stream() directly (if Gemini API key is configured).
2. FallbackLLMProvider error recovery (simulates a dead primary LLM and verifies fallback streaming).
3. get_streaming_llm() facade integration.
"""

import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/app")

from backend import config
from backend.LLM.providers.GeminiProvider import GeminiProvider
from backend.LLM.providers.LocalLLM import LocalLLMProvider
from backend.LLM.providers.fallback_provider import FallbackLLMProvider
from backend.services.llm import get_streaming_llm


def test_1_gemini_direct_stream():
    print("=" * 70)
    print("  TEST 1: DIRECT GEMINI PROVIDER STREAMING")
    print("=" * 70)

    gemini_key = config.GEMINI_API_KEY_1 or config.GEMINI_API_KEY_2
    if not gemini_key:
        print("[SKIP] No GEMINI_API_KEY configured in .env. Skipping direct Gemini test.")
        return

    gemini = GeminiProvider(model_name="gemini/gemini-3.1-flash-lite", temperature=0.7)
    prompt = "Explain in 3 concise bullet points why automated data validation is critical for enterprise software systems."
    print(f"Testing Gemini streaming directly with prompt: \"{prompt}\"\n")

    chunks = 0
    full_text = ""
    t0 = time.time()

    for event in gemini.generate_text_stream(prompt=prompt):
        chunks += 1
        content = event.get("content", "")
        sys.stdout.write(content)
        sys.stdout.flush()
        full_text += content

    duration = round(time.time() - t0, 2)
    print(f"\n\n[RESULTS] Chunks: {chunks}, Duration: {duration}s")
    assert chunks >= 2, f"Expected streaming chunks, got {chunks}"
    assert len(full_text.strip()) > 0, "Empty response from Gemini"
    print("[PASS] Gemini direct streaming works!")


def test_2_fallback_auto_recovery():
    print("\n" + "=" * 70)
    print("  TEST 2: FALLBACK PROVIDER AUTO-RECOVERY STREAMING")
    print("=" * 70)
    print("Simulating a broken primary provider (bad endpoint: http://localhost:99999)...")

    # Primary is broken / down
    broken_primary = LocalLLMProvider(
        model_name="ollama/qwen3:8b",
        api_base="http://localhost:99999"  # Deliberately dead host
    )
    # Secondary is working local LLM (or working provider)
    working_fallback = LocalLLMProvider(
        model_name=config.LOCAL_MODEL,
        api_base=config.OLLAMA_BASE_URL
    )

    fallback_wrapper = FallbackLLMProvider(
        primary_provider=broken_primary,
        fallback_provider=working_fallback
    )

    prompt = "Respond with: 'Fallback successfully caught the outage!'"
    print(f"Calling fallback_wrapper.generate_text_stream()...\n")

    chunks = 0
    full_text = ""
    t0 = time.time()

    for event in fallback_wrapper.generate_text_stream(prompt=prompt):
        chunks += 1
        content = event.get("content", "")
        if event.get("type") == "thinking":
            sys.stdout.write(f"\033[90m{content}\033[0m")
        else:
            sys.stdout.write(content)
        sys.stdout.flush()
        full_text += content

    duration = round(time.time() - t0, 2)
    print(f"\n\n[RESULTS] Chunks: {chunks}, Duration: {duration}s")
    assert chunks >= 2, f"Expected streaming chunks, got {chunks}"
    assert len(full_text.strip()) > 0, "Empty response from fallback"
    print("[PASS] Fallback provider successfully caught the dead primary and streamed from secondary!")


def test_3_facade_stream():
    print("\n" + "=" * 70)
    print("  TEST 3: GET_STREAMING_LLM() FACADE")
    print("=" * 70)

    provider = get_streaming_llm(temperature=0.7)
    print(f"Active Provider: {provider.__class__.__name__} (Model: {getattr(provider, 'model_name', 'N/A')})")

    prompt = "Give 3 quick tips for data quality."
    print(f"Prompt: \"{prompt}\"\n")

    chunks = 0
    t0 = time.time()
    for event in provider.generate_text_stream(prompt=prompt):
        chunks += 1
        content = event.get("content", "")
        if event.get("type") == "thinking":
            sys.stdout.write(f"\033[90m{content}\033[0m")
        else:
            sys.stdout.write(content)
        sys.stdout.flush()

    duration = round(time.time() - t0, 2)
    print(f"\n\n[RESULTS] Chunks: {chunks}, Duration: {duration}s")
    assert chunks >= 2, "Failed: Fewer than 2 chunks received in stream"
    print("[PASS] get_streaming_llm() facade works!")


if __name__ == "__main__":
    test_1_gemini_direct_stream()
    test_2_fallback_auto_recovery()
    test_3_facade_stream()
    print("\n" + "=" * 70)
    print("  ALL STEP 2 STREAMING TESTS PASSED SUCCESSFULLY! ✅")
    print("=" * 70)
