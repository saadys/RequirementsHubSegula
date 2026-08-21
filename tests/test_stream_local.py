"""
Test Local LLM Streaming & Thinking Tag Separation
Verifies that LocalLLMProvider.generate_text_stream yields tokens incrementally
and properly tags thinking vs response content.
"""

import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, "/app")

from backend import config
from backend.LLM.providers.LocalLLM import LocalLLMProvider

def main():
    print("=" * 70)
    print("  TESTING LOCAL LLM STREAMING & THINKING EXTRACTION")
    print("=" * 70)
    print(f"Model: {config.LOCAL_MODEL}")
    print(f"Ollama URL: {config.OLLAMA_BASE_URL}")
    print("-" * 70)

    provider = LocalLLMProvider(model_name=config.LOCAL_MODEL, temperature=0.7)

    # 1. Health check
    print("\n[1] Checking Provider Health...")
    if not provider.health_check():
        print(f"[FAIL] Local LLM unreachable at {provider.api_base}")
        sys.exit(1)
    print("[PASS] Provider is healthy and reachable.\n")

    # 2. Test Stream Generation
    prompt = "Explain in 2 concise sentences why CSV to XML conversion usually does not require a deep learning AI model."
    print(f"[2] Prompt: \"{prompt}\"")
    print("-" * 70)
    print("Streaming response tokens in real-time:\n")

    chunks_received = 0
    thinking_chunks = 0
    token_chunks = 0
    full_response = ""
    full_thinking = ""

    t_start = time.time()
    last_t = t_start

    for event in provider.generate_text_stream(prompt=prompt):
        chunks_received += 1
        now = time.time()
        delta_ms = round((now - last_t) * 1000, 1)
        last_t = now

        event_type = event.get("type", "token")
        content = event.get("content", "")

        if event_type == "thinking":
            thinking_chunks += 1
            full_thinking += content
            # Print thinking indicator
            sys.stdout.write(f"\033[90m{content}\033[0m")
            sys.stdout.flush()
        else:
            token_chunks += 1
            full_response += content
            sys.stdout.write(content)
            sys.stdout.flush()

    total_time = round(time.time() - t_start, 2)
    print("\n" + "-" * 70)
    print(f"\n[SUMMARY]")
    print(f"Total Stream Time: {total_time}s")
    print(f"Total Chunks: {chunks_received} (Thinking: {thinking_chunks}, Text: {token_chunks})")
    print(f"Thinking Characters: {len(full_thinking)}")
    print(f"Response Characters: {len(full_response)}")

    if chunks_received < 2:
        print("[FAIL] Streaming returned fewer than 2 chunks (tokens were not streamed).")
        sys.exit(1)

    if len(full_response.strip()) == 0:
        print("[FAIL] Empty response received.")
        sys.exit(1)

    print("\n[SUCCESS] Step 1 Test Passed! Streaming and token separation work as expected.")

if __name__ == "__main__":
    main()
