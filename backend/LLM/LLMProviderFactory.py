"""
LLM Provider Factory

Factory class responsible for instantiating LLM providers and setting up failover pipelines.
"""

from typing import Optional
from backend import config
from backend.LLM.LLMEnums import LLMProviderEnum
from backend.LLM.LLMInterfaces import LLMInterface
from backend.LLM.providers.GeminiProvider import GeminiProvider
from backend.LLM.providers.openai_provider import OpenAIProvider
from backend.LLM.providers.fallback_provider import FallbackLLMProvider


class LLMProviderFactory:
    """Factory for creating LLM Provider instances."""

    @staticmethod
    def get_provider(
        provider_type: Optional[LLMProviderEnum] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
    ) -> LLMInterface:
        """Instantiates provider with optional fallback based on configuration."""

        # Explicit OpenAI Provider requested
        if provider_type == LLMProviderEnum.OPENAI:
            model = model_name or config.FALLBACK_MODEL
            return OpenAIProvider(model_name=model, temperature=temperature)

        # Explicit Gemini Provider requested
        if provider_type == LLMProviderEnum.GEMINI:
            model = model_name or config.PRIMARY_MODEL
            return GeminiProvider(model_name=model, temperature=temperature)

        # Default Factory behavior: Gemini Primary + OpenAI Fallback (if OpenAI key present)
        primary_model = model_name or config.PRIMARY_MODEL
        primary_provider = GeminiProvider(model_name=primary_model, temperature=temperature)

        fallback_provider = None
        if config.OPENAI_API_KEY:
            fallback_provider = OpenAIProvider(model_name=config.FALLBACK_MODEL, temperature=temperature)

        return FallbackLLMProvider(
            primary_provider=primary_provider,
            fallback_provider=fallback_provider,
        )
