import litellm
from langchain_litellm import ChatLiteLLM
from backend import config

def get_llm() -> ChatLiteLLM:
    """Returns a ChatLiteLLM instance pointing at Gemini using the primary API key."""
    return ChatLiteLLM(
        model=config.PRIMARY_MODEL,
        api_key=config.GEMINI_API_KEY_1,
        temperature=config.LLM_TEMPERATURE,
    )
