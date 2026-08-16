"""
LLM Service Wrapper

Facade service exposing provider factory instances to pipeline nodes and services.
"""

from backend import config
from backend.LLM.LLMInterfaces import LLMInterface
from backend.LLM.LLMProviderFactory import LLMProviderFactory


def get_llm(temperature: float = config.LLM_TEMPERATURE) -> LLMInterface:
    """Returns an LLMInterface provider instance with multi-key and fallback support."""
    return LLMProviderFactory.get_provider(temperature=temperature)


def get_structured_llm() -> LLMInterface:
    """Returns an LLMInterface provider for structured fact extraction."""
    return get_llm(temperature=config.LLM_TEMPERATURE)


def get_clarification_llm() -> LLMInterface:
    """Returns an LLMInterface provider for clarification question generation."""
    return get_llm(temperature=config.LLM_TEMPERATURE_CLARIFICATION)


def get_streaming_llm(temperature: float = config.LLM_TEMPERATURE) -> LLMInterface:
    """Returns an LLMInterface provider for real-time token streaming with fallback support."""
    return get_llm(temperature=temperature)
