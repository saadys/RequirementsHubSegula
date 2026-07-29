"""
LiteLLM Router Setup

Configures multi-key, multi-provider LLM access with automatic
fallback when a key is exhausted.

Owner: Track A
"""

# TODO [Track A]: Implement LiteLLM Router
#
# 1. Import Router from litellm, ChatLiteLLMRouter from langchain_litellm
# 2. Configure model_list with Gemini keys + OpenAI fallback
# 3. Create router with fallback strategy
# 4. Create base llm (ChatLiteLLMRouter)
# 5. Create structured_llm = llm.with_structured_output(FactExtraction)
# 6. Create clarification_llm = llm.with_structured_output(ClarificationQuestions)
# 7. Export: get_llm(), get_structured_llm(), get_clarification_llm()
